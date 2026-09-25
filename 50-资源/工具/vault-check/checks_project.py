#!/usr/bin/env python3
"""项目引导口径检查:A7 路线一致性 / A9 索引页统计行。

A7 的取数来源是 `L.route_sources()`(根 `00-索引.md` + 各项目 `00-索引.md`,过渡期
再加旧的 `00-索引/系统.md`),标题同时认 `## 计划与进度` 与 `## 学习路线`(旧标题
常带注解,如 `## 学习路线(按序;…)`,故按子串查找)。

A9 项目索引页顶部统计行格式固定为:
    > 本项目知识 N 篇 · 状态 <status> · 覆盖 N/N(100%)
根 `00-索引.md` 汇总行格式固定为:
    > 全库知识 N 篇 · 项目 M 个  (知识数须等于各项目知识篇数之和)
旧 MOC 统计块仍由 `checks_extra.check_moc_stats()` 守(双口径并存,删旧 MOC 前不丢检查)。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

ROADMAP_HEADINGS = ("## 计划与进度", "## 学习路线")
PROJECT_STATS = re.compile(
    r"^>\s*本项目知识\s*(\d+)\s*篇\s*·\s*状态\s*([^\s·]+)\s*·\s*覆盖\s*(\d+)\s*/\s*(\d+)", re.M)
ROOT_STATS = re.compile(r"^>\s*全库知识\s*(\d+)\s*篇", re.M)


def _head(text: str, lines: int = 8) -> str:
    return "\n".join(text.splitlines()[:lines])


def roadmap_section(text: str) -> str:
    """路线小节(任一标题到下一个二级标题为止);都没有则空串。"""
    starts = [i for i in (text.find(h) for h in ROADMAP_HEADINGS) if i != -1]
    if not starts:
        return ""
    start = min(starts)
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def _project_of(path: Path) -> str:
    """path 所属项目名(只在 `10-项目/<名>/…` 下时非空,否则空串)。"""
    try:
        rel = path.resolve().relative_to((L.VAULT_ROOT / L.PROJECT_ROOT).resolve())
    except ValueError:
        return ""
    return rel.parts[0] if rel.parts else ""


def _listed_projects() -> set[str]:
    """各来源页路线小节里指到的项目(排除来源页所属项目自己链自己)。"""
    listed: set[str] = set()
    for src in L.route_sources():
        own = _project_of(src)
        for _, target in L.extract_links(roadmap_section(L.read_text(src))):
            bare = target.split("#")[0]
            if not bare:
                continue
            proj = _project_of(src.parent / bare)
            if proj and proj != own:
                listed.add(proj)
    return listed


def check_roadmap() -> list[L.Finding]:
    """A7:来源页里的项目条目与 10-项目 双向一致,且项目 status 与产出相符。

    正向:来源页里指向 10-项目 的链接必须存在(与 A1 有重叠,保留)。
    反向:每个含 !项目说明.md 的项目都在某来源页的路线小节里被指到。
    status:项目内除 !项目说明.md 外还有 .md(含 !实施计划.md,设计文档决策 3(c))→ learning,否则 todo。
    """
    out: list[L.Finding] = []
    sources = L.route_sources()
    for src in sources:
        rel = L.rel_path(src)
        for line, target in L.extract_links(L.read_text(src)):
            bare = target.split("#")[0]
            if "10-项目/" in bare and not (src.parent / bare).resolve().exists():
                out.append(L.Finding("A7", rel, line, target))
    anchor = L.rel_path(sources[0]) if sources else L.PROJECT_INDEX
    listed = _listed_projects()
    base = L.VAULT_ROOT / L.PROJECT_ROOT
    if not base.is_dir():
        return out
    for proj in sorted(base.iterdir()):
        fm_file = proj / "!项目说明.md"
        if not proj.is_dir() or not fm_file.exists():
            continue
        fm = L.parse_frontmatter(L.read_text(fm_file))
        if fm is None:
            continue  # 缺 frontmatter 由 A6 报,A7 不重复报
        status = fm.get("status", "").strip().strip('"').strip("'")
        others = [p for p in L.iter_md_files(proj)
                  if p.name != "!项目说明.md" and not L.is_teach_scaffold(L.rel_path(p))]
        expect = "learning" if others else "todo"
        if status not in ("done", "review") and status != expect:
            out.append(L.Finding("A7", L.rel_path(fm_file), 0,
                                 "status=%s 与项目内文件数不符(应为 %s)" % (status, expect)))
        if proj.name not in listed:
            out.append(L.Finding("A7", anchor, 0, "项目 %s 未进路线" % proj.name))
    return out


def _project_status(proj: Path) -> str:
    fm_file = proj / "!项目说明.md"
    if not fm_file.exists():
        return ""
    fm = L.parse_frontmatter(L.read_text(fm_file))
    return (fm or {}).get("status", "").strip().strip('"').strip("'")


def check_index_stats() -> list[L.Finding]:
    """A9(项目口径):项目索引页统计行的篇数/状态/覆盖须与实物一致;根汇总行须等于各项目之和。"""
    out: list[L.Finding] = []
    total = 0
    for _, kd in L.project_knowledge_dirs(L.VAULT_ROOT):
        index = kd.parent / L.PROJECT_INDEX
        files = sorted(kd.rglob("*.md"))
        total += len(files)
        if not index.exists():
            continue  # 缺索引由 A4 报,A9 不重复
        rel = L.rel_path(index)
        text = L.read_text(index)
        m = PROJECT_STATS.search(_head(text))
        if not m:
            out.append(L.Finding("A9", rel, 0,
                                 "缺统计行(`> 本项目知识 N 篇 · 状态 <status> · 覆盖 N/N(100%)`)"))
            continue
        covered = sum(1 for p in files if p.stem in text)
        if int(m.group(1)) != len(files):
            out.append(L.Finding("A9", rel, 0, "统计行知识 %s 篇与实物 %d 不符" % (m.group(1), len(files))))
        if (int(m.group(3)), int(m.group(4))) != (covered, len(files)):
            out.append(L.Finding("A9", rel, 0, "统计行覆盖 %s/%s 与实测 %d/%d 不符"
                                 % (m.group(3), m.group(4), covered, len(files))))
        status = _project_status(kd.parent)
        if status and m.group(2) != status:
            out.append(L.Finding("A9", rel, 0, "统计行状态 %s 与 !项目说明.md 的 %s 不符" % (m.group(2), status)))
    root_index = L.VAULT_ROOT / L.PROJECT_INDEX
    if root_index.exists():
        text = L.read_text(root_index)
        m = ROOT_STATS.search(_head(text))
        if not m:
            out.append(L.Finding("A9", L.rel_path(root_index), 0, "缺汇总行(`> 全库知识 N 篇 · 项目 M 个`)"))
        elif int(m.group(1)) != total:
            out.append(L.Finding("A9", L.rel_path(root_index), 0,
                                 "汇总行知识 %s 篇与各项目之和 %d 不符" % (m.group(1), total)))
    return out