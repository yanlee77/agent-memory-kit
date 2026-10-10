#!/usr/bin/env bash
# =====================================================================
# Agent Memory Kit · guard.sh  (account-independent memory guard)
# ---------------------------------------------------------------------
# 解决的核心问题：
#   AI 智能体的"长期记忆"大多放在平台配置目录里（如 ~/.workbuddy/memory），
#   这些目录**跟着登录账号走**——换账号、重装、平台清缓存，会被清空或覆盖。
#   本脚本维护一份放在平台目录**之外**的"真身(vault)"，保证记忆永不被账号切换抹掉。
#
# 三层：
#   工作副本 WORK   —— 智能体平时读写的那份（在平台目录内，可被清空，无所谓）
#   真身   VAULT   —— 账号无关、平台无关，平时的真身（只有合并、添加，从不删）
#   镜像   MIRROR  —— 另一块盘上的安全网（只补不删，防硬件损坏）
#
# 四条铁律：
#   1. 只合并、只添加，永不删除。任何一层被清空都不会连坐删另一层。
#   2. 锚点判定：WORK 缺 .vault-anchor 或串不匹配 = 被换账号重置 -> 从真身回灌。
#   3. 镜像只用"只补不删"，绝不用 /MIR（那会在本地被清时把镜像也删空）。
#   4. 顺序：先合并、后镜像。镜像必须放在合并之后，否则永远慢一轮。
#
# 调用：
#   bash guard.sh                 # 平时跑 = 双向合并；被清空时跑 = 从真身回灌
#   AMK_VAULT=/x/vault AMK_WORK=~/.agent-memory bash guard.sh   # 自定义路径
#
# 设计取向（来自实战教训，不折腾系统自动化）：
#   不挂开机启动项 / 计划任务。靠"每次对话结束自己跑一次" + 真身账号无关就够了。
# =====================================================================
set +e

# ---- 跨平台：git bash on Windows 需要关掉路径自动转换 ----
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) export MSYS_NO_PATHCONV=1; IS_WIN=1 ;;
  *) IS_WIN=0 ;;
esac

# ---- 配置（可用环境变量覆盖；否则用默认值） ----
VAULT="${AMK_VAULT:-$HOME/memory-vault}"        # 真身：账号无关，放在平台目录之外
WORK="${AMK_WORK:-$HOME/.agent-memory}"         # 工作副本：智能体平时读写
MIRROR="${AMK_MIRROR:-$HOME/memory-vault-mirror}" # 镜像：另一块盘（理想情况），只补不删
LOG="$VAULT/guard.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')
REPORT=""

# ---- 选同步工具 ----
if [ "$IS_WIN" = 1 ] && command -v robocopy >/dev/null 2>&1; then
  SYNC=robocopy
elif command -v rsync >/dev/null 2>&1; then
  SYNC=rsync
else
  SYNC=cp
fi

# ---- 同步原语 ----
# sync SRC DST MODE
#   MODE=merge   : 双向合并用——只拷较新、补独有，绝不删目标任何文件
#   MODE=restore : 复位回灌用——以 SRC 为准整体覆盖（只覆盖已存在/同名，不删目标独有文件）
sync() {
  local src="$1" dst="$2" mode="$3"
  [ -d "$src" ] || { mkdir -p "$dst" 2>/dev/null; return 0; }
  mkdir -p "$dst" 2>/dev/null
  case "$SYNC" in
    robocopy)
      # /E 含子目录；merge 加 /XO(只拷较新) 实现只增不删；restore 不加 /XO 全量覆盖
      if [ "$mode" = restore ]; then
        robocopy "$src" "$dst" /E /NFL /NDL /NP /R:1 /W:1 >/dev/null 2>&1
      else
        robocopy "$src" "$dst" /E /XO /NFL /NDL /NP /R:1 /W:1 >/dev/null 2>&1
      fi
      ;;
    rsync)
      if [ "$mode" = restore ]; then
        rsync -a "$src/" "$dst/" 2>/dev/null   # 覆盖同名，保留目标独有（不用 --delete）
      else
        rsync -a --update "$src/" "$dst/" 2>/dev/null  # 只拷较新，不删目标
      fi
      ;;
    cp)
      ( cd "$src" && find . -type f -print0 ) | while IFS= read -r -d '' f; do
        d="$dst/$f"
        mkdir -p "$(dirname "$d")" 2>/dev/null
        if [ "$mode" = merge ]; then
          if [ ! -f "$d" ] || [ "$src/$f" -nt "$d" ]; then
            cp -f "$src/$f" "$d" 2>/dev/null
          fi
        else
          cp -f "$src/$f" "$d" 2>/dev/null
        fi
      done
      ;;
  esac
}

# ---- 读取锚点串 ----
read_anchor() {
  local f="$1/.vault-anchor"
  [ -f "$f" ] && grep -m1 'VAULT-ANCHOR:' "$f" 2>/dev/null | cut -d: -f2-
}

# ---- 1) 判定工作副本是否被换账号重置 ----
TAG=$(read_anchor "$VAULT")
RESET=0; RMSG=""
if [ -z "$TAG" ]; then
  REPORT="$REPORT [警告] 真身无锚点(.vault-anchor)，跳过复位判定，按正常合并处理。"
elif [ ! -f "$WORK/.vault-anchor" ] || [ "$(read_anchor "$WORK")" != "$TAG" ]; then
  RESET=1
  RMSG="工作副本缺锚点或锚点串不匹配(期望 $TAG)"
fi

if [ "$RESET" -eq 1 ]; then
  # --- 被重置：先从真身整体回灌工作副本，再镜像（顺序不能反） ---
  sync "$VAULT" "$WORK" restore
  sync "$WORK" "$MIRROR" merge
  REPORT="$REPORT [防护触发] 工作副本被换账号重置($RMSG) -> 已从真身回灌; 镜像只补不删。"
else
  # --- 正常：双向合并(取较新、补独有、不删任一方)，最后再镜像 ---
  sync "$WORK" "$VAULT" merge
  sync "$VAULT" "$WORK" merge
  sync "$WORK" "$MIRROR" merge
  REPORT="$REPORT [正常合并] 工作副本<->真身双向合并(取较新); 镜像只补不删。"
fi

# ---- 2) 自检 ----
SC=$(find "$WORK" -type f 2>/dev/null | wc -l | tr -d ' ')
VC=$(find "$VAULT" -type f 2>/dev/null | wc -l | tr -d ' ')
BC=$(find "$MIRROR" -type f 2>/dev/null | wc -l | tr -d ' ')
OK="OK"; [ "${SC:-0}" -lt "${VC:-0}" ] && OK="!!工作副本少于真身!!"
REPORT="$REPORT 文件数[工作=$SC 真身=$VC 镜像=$BC] $OK"

mkdir -p "$VAULT" 2>/dev/null
echo "$TS $REPORT" >> "$LOG"
echo "GUARD: $REPORT"
