#!/usr/bin/env python3
"""0-Note 巡检扩展：A8 标签规范 / A10 知识归属（项目与容器的 `20-知识/`）。

A11(教学工作区完整性)在 `checks_teach.py`。旧「MOC 统计块」那一套(A9 的 MOC 口径、
`--coverage` / `--moc-stats` 两个开关)随 `00-索引/` 目录删除在 2026-09-25 收尾轮整块清掉：
A9 现在只剩项目口径，在 `checks_project.check_index_stats()`。

设计要点(2026-09-23 加，补上“巡检器不校验 tags”的缺口)：

- A8 报「同一标签的全库多种大小写写法」(例:windows 与 Windows 并存)。
  规则来源是库内约定"英文标签统一小写";用"大小写冲突"而不是"必须全小写"来判,
  是为了不误伤 Linux / RFID / Zephyr 这类按官方写法保留的专名 —— 只有当同一个小写
  形式在别处也出现过时,大写写法才算违规。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

TAGS_LINE = re.compile(r"^tags:\s*(.+)$", re.M)

def _head(text: str, lines: int = 8) -> str:
    return "\n".join(text.splitlines()[:lines])


def _tags_values(raw: str) -> list[str]:
    m = re.match(r"^\[(.*)\]\s*$", raw.strip())
    if not m:
        return []
    return [t.strip().strip('"').strip("'") for t in m.group(1).split(",") if t.strip()]


def check_tags() -> list[L.Finding]:
    """A8:tags 形状合法,且同一个小写形式不得同时存在多种大小写写法。

    注意别写成「把每个标签的小写形式都收集起来再比对」—— 那会让 A2 自己小写成 a2 后
    自己命中自己(2026-09-23 首版就踩了这个坑,报了 81 条假阳性)。必须只拿
    **真实存在的字面值**去比对。
    """
    out: list[L.Finding] = []
    rows: list[tuple[str, list[str]]] = []
    literals: set[str] = set()
    for p in L.iter_md_files(L.VAULT_ROOT):
        rel = L.rel_path(p)
        if L.is_fm_exempt(rel):
            continue
        text = L.read_text(p)
        if not text.startswith("---"):
            continue
        m = TAGS_LINE.search(_head(text, 12))
        if not m:
            continue
        raw = m.group(1)
        vals = _tags_values(raw)
        if not vals and raw.strip():
            out.append(L.Finding("A8", rel, 0, "tags 不是数组写法:%s" % raw.strip()[:40]))
            continue
        rows.append((rel, vals))
        literals |= set(vals)
    for rel, vals in rows:
        for v in vals:
            if v.isascii() and v != v.lower() and v.lower() in literals:
                out.append(L.Finding("A8", rel, 0,
                                     "标签 %s 与小写形式 %s 并存(库内约定英文标签小写)" % (v, v.lower())))
    return out


# 知识类 type：属成品正文，必须住进某个项目/容器的 `20-知识/` 目录
KNOWLEDGE_TYPES = ("algorithm", "language", "system", "concept", "tutorial")
# 归属判据：`10-项目/<项目或容器>/20-知识/…` —— `20-知识` 之前必须还有一层目录名。
# 只查「路径里有没有 `/20-知识/`」会把裸 `10-项目/20-知识/`(不属于任何项目)放行。
KNOWLEDGE_PATH = re.compile(r"^%s/[^/]+/%s/" % (re.escape(L.PROJECT_ROOT), re.escape(L.KNOWLEDGE_DIR)))


def check_project_layer_types() -> list[L.Finding]:
    """A10：项目层的知识类正文必须住进项目/容器的 `20-知识/`，不得散放其它位置。

    2026-09-25 反转(项目引导重构)：旧判据要求项目层知识搬去 `20-领域`，与新结构正好相反
    —— 知识搬进 `10-项目/<项目>/20-知识/` 后，旧判据会对每篇都报假阳性。现在只认一种合规
    形状：`10-项目/<某个目录>/20-知识/…`(项目与容器 `!名词解释` / `!系统与工具` 同理)；
    裸 `10-项目/20-知识/` 没有归属项目，不算合规。

    只认 `type` 字段：project(脚手架)、note(每日/清单)、log(记录)放哪都合规。
    """
    out: list[L.Finding] = []
    root = L.VAULT_ROOT / L.PROJECT_ROOT
    if not root.exists():
        return out
    for p in sorted(root.rglob("*.md")):
        fm = L.parse_frontmatter(L.read_text(p))
        if not fm:
            continue
        t = fm.get("type", "").strip().strip('"').strip("'")
        if t in KNOWLEDGE_TYPES and not KNOWLEDGE_PATH.match(L.rel_path(p)):
            out.append(L.Finding("A10", L.rel_path(p), 0,
                                 "type=%s 属成品知识，应放 %s/ 目录" % (t, L.KNOWLEDGE_DIR)))
    return out
