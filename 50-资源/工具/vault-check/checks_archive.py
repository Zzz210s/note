#!/usr/bin/env python3
"""A12 归档判据:两条口径,一条是**提示**(不算错误),一条是**错误**。

一、可归档提示(不是错误)。`archive_ready(proj)` 四条全满足才算可归档,缺一即否:
    ① `!项目说明.md` 的 frontmatter `status` 是 `done`
    ② 「出口」或「验收」段内没有未勾选任务项(`- [ ]`)
    ③ 正文含「复盘」小节(标题或粗体标签里带「复盘」)
    ④ 「任务清单」段内没有未勾选任务项
缺节按「不满足」处理:没有「验收/出口」或「任务清单」小节时无从验证收尾,宁可不出提示,
也不给假提示(提示是要人动手搬家的,误报比漏报贵)。命中者由 `archive_hints()` 汇总成
`可归档:<项目名>` 行,由 `check_vault.py` 打印在独立小节并**排除出 FAIL 计数** ——
未归档不是库的毛病,只是该有人收尾了。

二、反向检查(错误)。已在 `40-归档/` 下的项目(带 `!项目说明.md` 的目录)必须在根
`00-索引.md` 里留有一行登记;缺则报 A12。归档物若从索引入口消失,就成了找不回来的死文件。

小节切分:`sections()` 只认行首标题与整行粗体标签(`- **验收:**` / `1. **验收:**`);标题小节延伸
到下一个层级不高于它的标题(所以 `## 任务清单` 下的 `### 阶段二` 里的未勾选项仍算任务清单内),
粗体标签小节延伸到下一个任意标题/标签。行内粗体(`- **状态:** 进行中`)不算小节。扫判据前先
`L.strip_code()` 抹掉围栏/行内代码:示例里的 `- [ ]` 不该拦住归档,代码里的 `## 任务清单` 也不该
凭空造出小节。
"""
from __future__ import annotations

import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

INSTRUCTION = "!项目说明.md"
ARCHIVE_ROOT = "40-归档"
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
LABEL = re.compile(r"^[ \t]*(?:[-*+][ \t]+|\d+\.[ \t]+)?\*\*([^*]+)\*\*[ \t]*[:：]?[ \t]*$")
UNCHECKED = re.compile(r"^[ \t]*[-*+][ \t]+\[[ \t]\]", re.M)
LABEL_RANK = 99  # 粗体标签小节:碰到下一个任意标题/标签就结束


def sections(text: str, keyword: str) -> list[str]:
    """正文里所有标题(或整行粗体标签)含 keyword 的小节正文(含起始行)。"""
    lines = text.splitlines()
    starts: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m:
            starts.append((i, len(m.group(1)), m.group(2)))
            continue
        m = LABEL.match(line)
        if m:
            starts.append((i, LABEL_RANK, m.group(1)))
    out: list[str] = []
    for k, (i, level, title) in enumerate(starts):
        if keyword not in title:
            continue
        end = len(lines)
        for j, other, _ in starts[k + 1:]:
            if other <= level:
                end = j
                break
        out.append("\n".join(lines[i:end]))
    return out


def _closed(text: str, *keywords: str) -> bool:
    """含任一关键词的小节都存在,且都没有未勾选任务项。"""
    found = [s for k in keywords for s in sections(text, k)]
    return bool(found) and not any(UNCHECKED.search(s) for s in found)


def archive_ready(proj: Path) -> bool:
    """四条判据全满足才算「可归档」(判据见模块 docstring;缺节视为不满足)。"""
    spec = proj / INSTRUCTION
    if not spec.is_file():
        return False
    raw = L.read_text(spec)
    fm = L.parse_frontmatter(raw) or {}
    if fm.get("status", "").strip().strip('"').strip("'") != "done":
        return False
    text = L.strip_code(raw)   # 代码示例里的勾选框/标题不参与判据
    return (_closed(text, "出口", "验收") and bool(sections(text, "复盘"))
            and _closed(text, "任务清单"))


def archive_hints(verbose: bool = True) -> list[str]:
    """提示通道:可直接打印的行。无可归档项目时返回 `[]`(真库当前即如此)。

    `verbose=False` 只给一行计数(给 `--quiet` 用)。返回值不是 Finding,调用方不得计入 FAIL。
    """
    ready = sorted(p.name for p in L.project_dirs(L.VAULT_ROOT) if archive_ready(p))
    if not ready:
        return []
    out = ["[提示] 可归档项目 %d 个(提示,不计入 FAIL)" % len(ready)]
    if verbose:
        out.extend("   可归档:%s" % name for name in ready)
    return out


def _index_names(name: str) -> set[str]:
    """归档目录名的候选写法:全名 + 去掉日期/季度后缀的简称(`甲-2026Q1` → `甲`)。"""
    head, _, tail = name.rpartition("-")
    return {name, head} if head and tail[:1].isdigit() else {name}


def check_archive_ready() -> list[L.Finding]:
    """A12(错误):`40-归档/` 下的项目必须在根 `00-索引.md` 留有一行登记。

    归档项目按 `40-归档/**/!项目说明.md` 认(真库的 `40-归档/CSDN文章/` 是普通文件夹,
    不是项目,不该被要求登记)。可归档**提示**不在这里(见 `archive_hints()`),否则会让巡检 FAIL。
    """
    base = L.VAULT_ROOT / ARCHIVE_ROOT
    if not base.is_dir():
        return []
    archived = sorted({p.parent.name for p in base.rglob(INSTRUCTION)})
    if not archived:
        return []
    index = L.VAULT_ROOT / L.PROJECT_INDEX
    text = L.read_text(index) if index.is_file() else ""
    rel = L.rel_path(index)
    return [L.Finding("A12", rel, 0, "归档项目 %s 未在根 %s 登记" % (name, L.PROJECT_INDEX))
            for name in archived
            if not any(c in text for c in _index_names(name))]
