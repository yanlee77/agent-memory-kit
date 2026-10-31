#!/usr/bin/env python3
# init_memory.py —— Agent Memory Kit 骨架生成 + 跨索引检索
# 纯标准库，跨平台（Windows / macOS / Linux 均可）。
# 用法：
#   python init_memory.py --root ~/.agent-memory                     # 生成工作副本骨架
#   python init_memory.py --root ~/.agent-memory --vault ~/memory-vault  # 同时初始化账号无关真身
#   python init_memory.py --root ~/.agent-memory --search "GGUF"     # 跨索引检索
import argparse
import os
import secrets
import sys

TEMPLATES = {
    "MEMORY.md": """# MEMORY.md（主记忆）

> 只放原则与态度，不堆流水账。替换为你的真实内容，绝不含密钥/私人路径/业务流程。

## 一、身份
- 智能体：___。用户：___。

## 二、硬约束
1. 脱敏红线：密钥/token/密码/私钥/云凭证/真实私人路径/业务流程，一律不写不提交。
2. 有风险的删除：先改名，确认无问题再删。
3. 不凭印象说进度：开场先读记忆。
4. 纠错当场改回原处并标注。

## 三、对事的态度
1. 真的有用，不表演有用。
2. 有观点也诚实。
3. 先自己想办法，再开口问。

## 四、记忆法（写、读、删各一条判据）
- **写**：原则留主记忆、技法进 skill、过程留分记忆、入口进索引；判据是「**只有哪一处会被改到**」——两处都会被改就是分叉。
- **读**：走薄路径（本文件 + 当日分记忆 + 这件事的 skill）；**索引只查不读**（`--search` 拿行号再定点读）。
- **删**：只有**索引层的任务行**能清（已执行完／挂起超 10 天没再进行，天数按**最后一次有动作**算），
  清之前整段抄进归档文件；**原则、分记忆原文、技法结论、"别再回头"的停止项永不删**。
- 细节见 `加载与检索纪律.md` / `主记忆瘦身法.md`。
""",
    "索引_按时间.md": "# 索引_按时间\n\n> 只查不读：`python init_memory.py --search \"YYYY-MM-DD\"` 拿行号，再定点读那几十行。\n\n## YYYY-MM-DD\n- （按时间轴记要点，跨事件细节去 索引_按事件）\n",
    "索引_按事件.md": "# 索引_按事件\n\n> 只查不读：先 `--search \"事件名\"` 拿行号，再定点读那一节。\n\n## 事件：___\n- YYYY-MM-DD：___\n",
    "索引_按技法（关键词）.md": "# 索引_按技法（关键词）\n\n> 只查不读：先 `--search \"关键词\"` 拿行号；这本最容易涨到几万字符，禁止整本灌。\n\n| 关键词 | 落点 |\n|--------|------|\n| ___ | ___ |\n",
    "索引_按状态.md": "# 索引_按状态（什么没完、卡在哪）\n\n> 只查不读：每天开工必读，更要省着读——先 `--search \"事项\"` 拿行号。\n\n| 事项 | 状态 | 卡在哪 / 下一步 | 落点 |\n|------|------|----------------|------|\n| ___ | 待办 | ___ | ___ |\n",
    "索引_按人物.md": "# 索引_按人物（谁说过什么、谁拍的板）\n\n> 只查不读：先 `--search \"人名\"` 拿行号。分清三件事：谁的观察、谁的判断、谁的拍板。\n\n| 谁 | 角色 / 边界 | 关键原话（照录不润色） | 拍板了什么 |\n|----|------------|----------------------|------------|\n| ___ | ___ | ___ | ___ |\n",
}

INDEX_FILES = list(TEMPLATES.keys())


def make_anchor() -> str:
    """生成一个随机锚点串，用于 guard.sh 判定工作副本是否被换账号重置。"""
    return "VAULT-ANCHOR:" + secrets.token_hex(8)


def write_anchor(root: str, tag: str) -> None:
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, ".vault-anchor"), "w", encoding="utf-8") as f:
        f.write(f"{tag}\n")
    print(f"  锚点: {root}/.vault-anchor ({tag})")


def init(root: str, vault: str | None = None) -> None:
    tag = make_anchor()
    os.makedirs(root, exist_ok=True)
    for name, content in TEMPLATES.items():
        path = os.path.join(root, name)
        if os.path.exists(path):
            print(f"  跳过（已存在）: {path}")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  生成: {path}")
    write_anchor(root, tag)

    if vault:
        # 真身：账号无关、平台无关。用同一锚点，guard.sh 才能比对复位。
        os.makedirs(vault, exist_ok=True)
        for name, content in TEMPLATES.items():
            vpath = os.path.join(vault, name)
            if os.path.exists(vpath):
                print(f"  跳过（已存在）: {vpath}")
            else:
                with open(vpath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  生成: {vpath}")
        write_anchor(vault, tag)
        print(f"\n真身已就绪：{vault}（放在平台配置目录之外，账号无关）")

    print(f"\n骨架已就绪：{root}")
    print("下一步：填 MEMORY.md 身份与硬约束；日常写三个索引 + 按日期分记忆。")
    print("每次对话结束跑一次 bash guard.sh，把工作副本同步进真身。")


def search(root: str, keyword: str) -> None:
    hits = 0
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.startswith(".") or not fn.endswith(".md"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if keyword in line:
                            print(f"{fp}:{i}: {line.rstrip()}")
                            hits += 1
            except (OSError, UnicodeDecodeError):
                continue
    print(f"\n关键词 '{keyword}' 命中 {hits} 处。")


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent Memory Kit 工具")
    ap.add_argument("--root", default="~/.agent-memory", help="工作副本记忆根目录")
    ap.add_argument("--vault", help="真身目录（账号无关，放在平台配置目录之外）；"
                                     "指定后会同时初始化真身骨架并写入同一锚点")
    ap.add_argument("--search", help="跨索引检索关键词")
    args = ap.parse_args()
    root = os.path.expanduser(args.root)
    vault = os.path.expanduser(args.vault) if args.vault else None
    if args.search:
        search(root, args.search)
    else:
        init(root, vault)
    return 0


if __name__ == "__main__":
    sys.exit(main())
