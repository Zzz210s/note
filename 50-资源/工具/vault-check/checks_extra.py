#!/usr/bin/env python3
"""0-Note 巡检扩展:A8 标签规范 / A9 MOC 统计块一致性 / A10 项目层不得存知识笔记 / --coverage 覆盖率。

设计要点(2026-09-23 加,补上原来"巡检器不校验 tags、统计块只靠人肉"的两个缺口):

- A8 报「同一标签的全库多种大小写写法」(例:windows 与 Windows 并存)。
  规则来源是库内约定"英文标签统一小写";用"大小写冲突"而不是"必须全小写"来判,
  是为了不误伤 Linux / RFID / Zephyr 这类按官方写法保留的专名 —— 只有当同一个小写
  形式在别处也出现过时,大写写法才算违规。
- A9 把 MOC 顶部统计块的「条目数」与「覆盖率末对 n/m」跟实测对齐。
  这一条正是之前漏掉的那个缺陷(统计块写 45、实物 46),现在由脚本兜住。
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

# 统计块:第一段是条目数,最后出现的一组 n/m 是"覆盖篇数/目录总篇数"
STATS_ENTRY = re.compile(r"^>\s*条目\s*(\d+)", re.M)
PAIR = re.compile(r"(\d+)\s*/\s*(\d+)")
CHECK_DATE = re.compile(r"最后校验\s*(\d{4}-\d{2}-\d{2})")
TAGS_LINE = re.compile(r"^tags:\s*(.+)$", re.M)

# 各 MOC 的覆盖目录(与 MOC 统计块里写的口径一致;改口径时两处一起改)
MOC_DIRS: dict[str, tuple[str, ...]] = {
    "算法.md": ("20-领域/01-算法",),
    "编程语言.md": ("20-领域/02-编程语言", "20-领域/03-开发工具", "50-资源/工具"),
    "系统.md": ("20-领域/04-系统与部署", "20-领域/05-网络与服务器", "20-领域/06-网页开发",
                "10-项目/!问题追踪", "50-资源/记录", "50-资源/Zephyr", "20-领域/08-数据库"),
    "外语.md": ("20-领域/07-外语", "10-项目/2026-掌握西班牙语B2",
                "10-项目/!六级英语每日一练"),
    "AI-agent.md": ("20-领域/09-AI智能体",),
}

FM_EXEMPT = ("00-索引/", "90-模板/", "README", "10-项目/!问题追踪/")


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
        if any(rel.startswith(e) for e in FM_EXEMPT):
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


def coverage(moc_name: str) -> tuple[int, int]:
    """(已登记篇数, 目录内 md 总数)。登记口径与 A4 相同:文件名出现在该 MOC 文本里。"""
    moc = L.VAULT_ROOT / "00-索引" / moc_name
    if not moc.exists() or moc_name not in MOC_DIRS:
        return 0, 0
    blob = L.read_text(moc)
    total = 0
    covered = 0
    for d in MOC_DIRS[moc_name]:
        root = L.VAULT_ROOT / d
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.md")):
            total += 1
            if p.name in blob:
                covered += 1
    return covered, total


def moc_entry_count(moc_name: str) -> int:
    """按统计块同一口径数条目:MOC 文本里以 `- [` 开头的行。"""
    moc = L.VAULT_ROOT / "00-索引" / moc_name
    if not moc.exists():
        return 0
    return sum(1 for ln in L.read_text(moc).splitlines() if ln.startswith("- ["))


def check_moc_stats() -> list[L.Finding]:
    """A9:MOC 统计块的条目数与覆盖率末对必须与实测一致,日期格式必须合法。"""
    out: list[L.Finding] = []
    for moc in sorted((L.VAULT_ROOT / "00-索引").glob("*.md")):
        rel = L.rel_path(moc)
        head = _head(L.read_text(moc))
        m = STATS_ENTRY.search(head)
        if not m:
            out.append(L.Finding("A9", rel, 0, "缺统计块(H1 下应有 `> 条目 N · 覆盖 … · 最后校验 YYYY-MM-DD`)"))
            continue
        actual = moc_entry_count(moc.name)
        if int(m.group(1)) != actual:
            out.append(L.Finding("A9", rel, 0, "统计块条目 %s 与实测 %d 不符" % (m.group(1), actual)))
        pairs = PAIR.findall(head.split("\n", 3)[2] if len(head.split("\n", 3)) > 2 else head)
        if pairs:
            cov_s, tot_s = pairs[-1]
            cov, tot = coverage(moc.name)
            if (int(cov_s), int(tot_s)) != (cov, tot):
                out.append(L.Finding("A9", rel, 0,
                                     "统计块覆盖率 %s/%s 与实测 %d/%d 不符" % (cov_s, tot_s, cov, tot)))
        if not CHECK_DATE.search(head):
            out.append(L.Finding("A9", rel, 0, "统计块缺「最后校验 YYYY-MM-DD」"))
    return out


# 知识类 type:出现这些就说明成品正文写在了项目层(README:20-领域 是正文唯一存放处)
KNOWLEDGE_TYPES = ("algorithm", "language", "system", "concept", "tutorial")


def check_project_layer_types() -> list[L.Finding]:
    """A10:项目层(10-项目)不得存成品知识笔记。

    2026-09-23 定:那次审查发现项目层躺着 22 篇 type 为知识类的成品正文(西语词汇/语法/教材笔记、
    算法题解、SQLite 介绍、Zephyr 全貌、六级笔记),全靠人眼才看出来。这条把它变成自动门禁。

    只认 `type` 字段:project(脚手架)、note(项目内每日/清单)、log(记录)留在项目层是合规的
    (README 已如此定义)。若某篇确实只服务于本项目,把 type 改成 note 或 log 即可,不必搬家。
    """
    out: list[L.Finding] = []
    root = L.VAULT_ROOT / "10-项目"
    if not root.exists():
        return out
    for p in sorted(root.rglob("*.md")):
        fm = L.parse_frontmatter(L.read_text(p))
        if not fm:
            continue
        t = fm.get("type", "").strip().strip('"').strip("'")
        if t in KNOWLEDGE_TYPES:
            out.append(L.Finding("A10", L.rel_path(p), 0,
                                 "type=%s 属成品知识,应放 20-领域(README 分层规则)" % t))
    return out


def coverage_lines() -> list[str]:
    """--coverage 的输出:逐 MOC 的条目数、覆盖率与未登记清单。"""
    lines: list[str] = []
    for moc in sorted((L.VAULT_ROOT / "00-索引").glob("*.md")):
        cov, tot = coverage(moc.name)
        pct = (100.0 * cov / tot) if tot else 100.0
        lines.append("%s  条目 %d  覆盖 %d/%d(%.0f%%)" % (moc.name, moc_entry_count(moc.name), cov, tot, pct))
        if moc.name in MOC_DIRS:
            blob = L.read_text(moc)
            for d in MOC_DIRS[moc.name]:
                root = L.VAULT_ROOT / d
                if not root.exists():
                    continue
                for p in sorted(root.rglob("*.md")):
                    if p.name not in blob:
                        lines.append("    未登记:%s" % L.rel_path(p))
    return lines
