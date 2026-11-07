#!/usr/bin/env python3
# init_memory.py —— Agent Memory Kit 骨架生成 + 跨索引检索 + V2.0 结构层审计
# 纯标准库，跨平台（Windows / macOS / Linux 均可）。
# 用法：
#   python init_memory.py --root ~/.agent-memory                     # 生成工作副本骨架
#   python init_memory.py --root ~/.agent-memory --vault ~/memory-vault  # 同时初始化账号无关真身
#   python init_memory.py --root ~/.agent-memory --search "关键词"    # 跨索引检索
#   python init_memory.py --root ~/.agent-memory --audit             # V2.0：倒排总表四项体检
import argparse
import os
import re
import secrets
import sys
from collections import Counter

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
- **★ 索引＝倒排指针，不是副本（V2.0）**：一条事实只在分记忆写一次，按真实维度生成 N 条指针；
  **时间索引是主根**，其他索引都指向它，两跳到位，不许直连分记忆。详见 `立体索引结构化法.md`。
- **★ 整理时删重复是常规原则（V2.0）**：删的是副本与重复指针，不是事实本身；
  多实例并发靠「写入时唯一键」在落笔那一刻挡住，别等收工靠人眼比对。
- **读**：走薄路径（本文件 + 当日分记忆 + 这件事的 skill）；**索引只查不读**（`--search` 拿行号再定点读）。
- **删**：只有**索引层的任务行**能清（已执行完／挂起超 10 天没再进行，天数按**最后一次有动作**算），
  清之前整段抄进归档文件；**原则、分记忆原文、技法结论、"别再回头"的停止项永不删**。
- 细节见 `加载与检索纪律.md` / `主记忆瘦身法.md` / `立体索引结构化法.md`。
""",
    "索引_按时间.md": """# 索引_按时间（★ V2.0 起是主根）

> 只查不读：`--search "YYYY-MM-DD"` 拿行号，再定点读那几十行。
> **★ 其他索引指向具体内容时，都先到这里的时间根键，再由本表一步给分记忆物理锚点（两跳解析）。**
> 物理路径全系统只在本表出现一次；分记忆重整只改本表一行，其他轴不动。

## ★ 时间根锚点表（唯一登记处）

| 时间根键 | 日期 | 事件摘要 | 分记忆物理锚点 | status |
|---|---|---|---|---|
| `T/YYYY-MM-DD/E1` | YYYY-MM-DD | （一句话，不写过程） | `YYYY-MM-DD.md#L<n>` | 现行 |

## YYYY-MM-DD
- （按时间轴记要点，跨事件细节去 索引_立体网格 / 索引_按事件）
""",
    "索引_按事件.md": "# 索引_按事件\n\n> 只查不读：先 `--search \"事件名\"` 拿行号，再定点读那一节。\n> V2.0 起**大事件索引只列分事件**，具体事件入口去 `索引_立体网格.md`。\n\n## 事件：___\n- YYYY-MM-DD：___\n",
    "索引_按技法（关键词）.md": "# 索引_按技法（关键词）\n\n> 只查不读：先 `--search \"关键词\"` 拿行号；这本最容易涨到几万字符，禁止整本灌。\n\n| 关键词 | 落点 |\n|--------|------|\n| ___ | ___ |\n",
    "索引_按状态.md": "# 索引_按状态（什么没完、卡在哪）\n\n> 只查不读：每天开工必读，更要省着读——先 `--search \"事项\"` 拿行号。\n\n| 事项 | 状态 | 卡在哪 / 下一步 | 落点 |\n|------|------|----------------|------|\n| ___ | 待办 | ___ | ___ |\n",
    "索引_按人物.md": "# 索引_按人物（谁说过什么、谁拍的板）\n\n> 只查不读：先 `--search \"人名\"` 拿行号。分清三件事：谁的观察、谁的判断、谁的拍板。\n\n| 谁 | 角色 / 边界 | 关键原话（照录不润色） | 拍板了什么 |\n|----|------------|----------------------|------------|\n| ___ | ___ | ___ | ___ |\n",
    "索引_立体网格.md": """# 索引_立体网格（V2.0 倒排总表）

> **只查不读。本表是指针，不是副本。** 一个事件的事实只在分记忆存一次；
> 每行 `fact` 都填同一个时间根键 ⇒ 从任一根轴摸进去，到的都是同一份记忆。
> 字段：date | axis | path | keys | fact | target | status | valid_from | invalid_at
> 唯一键：axis|path|fact|keys （写入前算指纹，命中即跳过）
> **体量以 stat 为准，不写死数字**；整行 ≤200 字、keys ≤40 字。
> 只有「时间」轴那行写分记忆物理锚点，其余各行 target 一律指 `索引_按时间.md#<根键>`。

## 零、时间主根（唯一登记处在 索引_按时间.md#时间根锚点表）

| 时间根键 | 日期 | 事件摘要 | 物理锚点（主根给出） |
|---|---|---|---|
| `T/YYYY-MM-DD/E1` | YYYY-MM-DD | （一句话） | `YYYY-MM-DD.md#L<n>` |

## 一、大事件目录（只列分事件，可由 path 前两级聚合重建）

| 大事件 | 分事件 |
|---|---|
| `事件/<大类>` | `<分事件 A>` ／ `<分事件 B>` |

## 二、倒排指针（一行一入口）

```text
YYYY-MM-DD | 时间 | 时间/YYYY-MM/YYYY-MM-DD | <关键词> | T/YYYY-MM-DD/E1 | YYYY-MM-DD.md#L<n> | 现行 | YYYY-MM-DD | -
YYYY-MM-DD | 事件 | 事件/<大类>/<分事件> | <关键词> | T/YYYY-MM-DD/E1 | 索引_按时间.md#T/YYYY-MM-DD/E1 | 现行 | YYYY-MM-DD | -
YYYY-MM-DD | 经验 | 经验/<大类>/<主题> | <可复用判断> | T/YYYY-MM-DD/E1 | 索引_按时间.md#T/YYYY-MM-DD/E1 | 现行 | YYYY-MM-DD | -
YYYY-MM-DD | 失败 | 失败/<大类>/<主题> | trigger:<触发场景> | T/YYYY-MM-DD/E1 | 索引_按时间.md#T/YYYY-MM-DD/E1 | 现行 | YYYY-MM-DD | -
YYYY-MM-DD | 技能 | 技能/<技能名> | <现行节> | T/YYYY-MM-DD/E1 | 索引_按时间.md#T/YYYY-MM-DD/E1 | 现行 | YYYY-MM-DD | -
```

（以上是占位模板；实际落盘把日期换成真实日期、fact 换成主根表已登记的键。`--audit` 忽略占位行。）

## 三、查询 / 维护

- `grep -F "| 失败 |" 索引_立体网格.md` → 失败轴视图；
  `grep -F "T/.../E1" 索引_立体网格.md` → 一个事实的全部维度（倒排反查）；
  `grep -F "T/.../E1" 索引_按时间.md` → 第 2 跳主根表直接给物理锚点。
- 收工顺序不能反：分记忆正文 → 主根登记 → 补 N 行指针（唯一键去重）→ `--audit` → `guard.sh`。
- 纠正＝填 `invalid_at` + 改 `status`，**关闭区间不删行**；默认检索只出「现行」。
""",
}

INDEX_FILES = list(TEMPLATES.keys())
DATE_RE = re.compile(r"20\d\d-\d\d-\d\d")
ROOTKEY_RE = re.compile(r"^T/20\d\d-\d\d-\d\d/E\d+$")
FACTFILE_RE = re.compile(r"20\d\d-\d\d-\d\d\.md#L\d+")


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
    print("下一步：填 MEMORY.md 身份与硬约束。")
    print("★ V2.0 落盘顺序：事实写分记忆一次 → 索引_按时间 主根表登记 → 索引_立体网格 补 N 行指针 → --audit → guard.sh")
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


def audit(root: str) -> None:
    """V2.0 常驻审计：超长行 / 重复唯一键 / 未登记根键 / 绕过主根 / 体量上限 / 两跳。"""
    grid = os.path.join(root, "索引_立体网格.md")
    tim = os.path.join(root, "索引_按时间.md")
    mem = os.path.join(root, "MEMORY.md")
    if not os.path.exists(grid):
        print("未找到 索引_立体网格.md；先跑 init_memory.py 生成骨架。")
        return
    text = open(grid, encoding="utf-8").read()
    root_text = open(tim, encoding="utf-8").read() if os.path.exists(tim) else ""
    ptr = []
    for i, line in enumerate(text.splitlines(), 1):
        p = [x.strip() for x in line.split("|")]
        if len(p) == 9 and DATE_RE.fullmatch(p[0]):
            ptr.append((i, line, p))
    print("=== V2.0 audit（立体倒排总表） ===")
    print("指针 %d 条 / 总表 %d B / 主记忆 %d B / 上限(×2) %d B" %
          (len(ptr), os.path.getsize(grid),
           os.path.getsize(mem) if os.path.exists(mem) else 0,
           (os.path.getsize(mem) * 2) if os.path.exists(mem) else 0))
    long = [(i, len(l)) for i, l, _ in ptr if len(l) > 200]
    keyover = [(i, len(p[3])) for i, _, p in ptr if len(p[3]) > 40]
    keys = Counter("|".join((p[1], p[2], p[4], p[3])) for _, _, p in ptr)
    dup = [k for k, n in keys.items() if n > 1]
    orphan = [(i, p[4]) for i, _, p in ptr if not ROOTKEY_RE.match(p[4]) or p[4] not in root_text]
    bypass = [(i, p[1]) for i, _, p in ptr if FACTFILE_RE.search(p[5]) and p[1] != "时间"]
    noroot = [(i, p[1]) for i, _, p in ptr if p[1] != "时间" and not p[5].startswith("索引_按时间.md#")]
    bad = [(i, p[6]) for i, _, p in ptr if ("作废" in p[6] or "清账" in p[6]) and p[8] == "-"]
    for label, got in (("超长行 >200 字", long), ("keys >40 字", keyover),
                       ("重复唯一键", dup), ("未在主根登记", orphan),
                       ("非时间轴直连分记忆", bypass), ("非时间轴未指主根", noroot),
                       ("已作废却未填 invalid_at", bad)):
        print("  %-26s %d %s" % (label, len(got), "OK" if not got else "!! " + str(got[:3])))
    facts = Counter(p[4] for _, _, p in ptr)
    for f, n in facts.items():
        print("  倒排反查 %-24s → %d 条指针" % (f, n))
    cap = (os.path.getsize(mem) * 2) if os.path.exists(mem) else 0
    ok = not (long or keyover or dup or orphan or bypass or noroot or bad) and (not cap or os.path.getsize(grid) <= cap)
    print("  ⇒ " + ("OK（两跳以内、无任何越权）" if ok else "!! 有越权项，先修再同步"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent Memory Kit 工具")
    ap.add_argument("--root", default="~/.agent-memory", help="工作副本记忆根目录")
    ap.add_argument("--vault", help="真身目录（账号无关，放在平台配置目录之外）；"
                                     "指定后会同时初始化真身骨架并写入同一锚点")
    ap.add_argument("--search", help="跨索引检索关键词")
    ap.add_argument("--audit", action="store_true", help="V2.0：倒排总表四项体检")
    args = ap.parse_args()
    root = os.path.expanduser(args.root)
    vault = os.path.expanduser(args.vault) if args.vault else None
    if args.audit:
        audit(root)
    elif args.search:
        search(root, args.search)
    else:
        init(root, vault)
    return 0


if __name__ == "__main__":
    sys.exit(main())
