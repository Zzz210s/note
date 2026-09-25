#!/usr/bin/env python3
"""项目引导口径检查:A7 路线一致性 / A9 索引页统计行。

A7 的来源页 = `L.route_sources()`(根 `00-索引/00-索引.md` + 各项目 `00-索引.md`)。反向判定「项目是否已进路线」按来源页**全文**里指向该项目
`!项目说明.md` 的链接(同时认 `](...)` 与 `[[...]]`):只扫「计划与进度」小节会漏掉写在
表格/别处的条目,而 Task 8 生成的根索引两种写法都可能出现。零命中时只发一条汇总提示,
不逐项目刷「未进路线」。路线小节标题须是行首二级标题(`## 计划与进度` / `## 学习路线`,后者旧文本带注解,故按前缀匹配)。

A9 项目索引页统计行格式固定为:
    > 本项目知识 N 篇 · 状态 <status> · 覆盖 N/N(100%)
根 `00-索引/00-索引.md` 汇总行格式固定为:
    > 全库知识 N 篇 · 项目 M 个  (N=各项目 20-知识 篇数之和)
M 按 `10-项目/` 下含 `!项目说明.md` 的项目目录数校验(与 A7 的项目定义同源;`!问题追踪`
这类容器不算项目)。旧 MOC 统计块口径已随 `00-索引/` 删除在 2026-09-25 收尾轮清掉,
A9 现在只有下面这两种口径。
反向判定的结论对外暴露为 `roadmap_reported()`:A14① 据此避同因双报。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

ROADMAP_HEADING = re.compile(r"^##[ \t]+(?:计划与进度|学习路线)", re.M)
PROJECT_STATS = re.compile(
    r"^>\s*本项目知识\s*(\d+)\s*篇\s*·\s*状态\s*([^\s·]+)\s*·\s*覆盖\s*(\d+)\s*/\s*(\d+)", re.M)
ROOT_STATS = re.compile(r"^>\s*全库知识\s*(\d+)\s*篇(?:\s*·\s*项目\s*(\d+)\s*个)?", re.M)
INSTRUCTION = "!项目说明.md"


def _head(text: str, lines: int = 8) -> str:
    return "\n".join(text.splitlines()[:lines])


def roadmap_section(text: str) -> str:
    """路线小节(行首二级标题到下一个二级标题为止);没有则空串。"""
    m = ROADMAP_HEADING.search(text)
    if not m:
        return ""
    end = text.find("\n## ", m.start() + 1)
    return text[m.start():] if end == -1 else text[m.start():end]


def _project_of(path: Path) -> str:
    """path 所属项目名(只在 `10-项目/<名>/…` 下时非空,否则空串)。目标不必存在。"""
    try:
        rel = path.resolve().relative_to((L.VAULT_ROOT / L.PROJECT_ROOT).resolve())
    except ValueError:
        return ""
    return rel.parts[0] if rel.parts else ""


def _linked_project(src: Path, raw: str) -> str:
    """链接目标 → 项目名(仅当它指向 `10-项目/<项目>/!项目说明.md` 且非 src 自身项目时)。

    markdown 链接按来源页所在目录解析;wikilink 是库根相对
    (`[[10-项目/甲/!项目说明|甲]]`),故再按库根兜底一次。
    解析结果等于来源页自身项目的候选要**跳过并继续试下一个**:来源页在 `10-项目/乙/` 里写
    `[[10-项目/甲/!项目说明]]` 时,`src.parent / bare` 会解析成
    `10-项目/乙/10-项目/甲/!项目说明`,取首段仍是 `乙`——若就此 return,库根候选
    再没机会解析出 `甲`,`甲` 会被误报「未进路线」。
    """
    bare = raw.split("|")[0].split("#")[0].strip().lstrip("<").rstrip(">")
    if not bare or Path(bare).name not in (INSTRUCTION, "!项目说明"):
        return ""
    own = _project_of(src)
    for cand in (src.parent / bare, L.VAULT_ROOT / bare.lstrip("/")):
        proj = _project_of(cand)
        if proj and proj != own:
            return proj
    return ""


def _listed_projects() -> set[str]:
    """来源页全文里指到的项目(排除来源页链自己,避免自链把自身「洗白」)。"""
    listed: set[str] = set()
    for src in L.route_sources():
        own = _project_of(src)
        text = L.read_text(src)
        for _, target in list(L.extract_links(text)) + list(L.extract_wikilinks(text)):
            proj = _linked_project(src, target)
            if proj and proj != own:
                listed.add(proj)
    return listed


def roadmap_reported() -> set[str]:
    """A14① 用:A7 会点名「未进路线」的项目名(零命中时 A7 只发汇总,同样算覆盖)。"""
    listed = _listed_projects()
    return {p.name for p in L.project_dirs(L.VAULT_ROOT) if not listed or p.name not in listed}


def _no_project_hint(anchor: Path) -> str:
    """零命中时的提示后缀(顺带把「标题须是行首二级」落成可观测行为)。"""
    text = L.read_text(anchor) if anchor.exists() else ""
    if not ROADMAP_HEADING.search(text):
        return "且缺行首二级标题 `## 计划与进度`"
    body = roadmap_section(text).partition("\n")[2]
    if not body.strip():
        return "且「计划与进度」小节为空"
    return "且该小节未链接任何项目的 `!项目说明.md`"


def check_roadmap() -> list[L.Finding]:
    """A7:来源页里的项目条目与 10-项目 双向一致,且项目 status 与产出相符。

    正向:来源页全文里指向 `10-项目/` 的 md 链接必须可解析(与 A1 有重叠,保留)。
    反向:每个项目(含 `!项目说明.md` 的目录)都须在来源页全文里被指到。
    status:项目内除 `!项目说明.md` 与 `00-索引.md` 外还有 .md(含 `!实施计划.md`,设计文档决策 3(c))→ learning,否则 todo。
    索引页不算「产出」:Task 8 给每个项目都建了 `00-索引.md`,若计入则 todo 状态永不出现。
    """
    out: list[L.Finding] = []
    sources = L.route_sources()
    for src in sources:
        rel = L.rel_path(src)
        for line, target in L.extract_links(L.read_text(src)):
            bare = target.split("#")[0]
            if "10-项目/" in bare and not (src.parent / bare).resolve().exists():
                out.append(L.Finding("A7", rel, line, target))
    anchor_path = sources[0] if sources else L.VAULT_ROOT / L.ROOT_INDEX
    anchor = L.rel_path(anchor_path) if sources else L.ROOT_INDEX
    projects = L.project_dirs(L.VAULT_ROOT)
    if not projects:
        return out
    listed = _listed_projects()
    quiet = not listed  # 一个都没列出:只发汇总提示,不逐项目刷屏
    if quiet:
        out.append(L.Finding("A7", anchor, 0, "来源页全文未列出任何项目(%d 个),%s"
                             % (len(projects), _no_project_hint(anchor_path))))
    for proj in projects:
        fm_file = proj / INSTRUCTION
        fm = L.parse_frontmatter(L.read_text(fm_file))
        if fm is None:
            continue  # 缺 frontmatter 由 A6 报,A7 不重复报
        status = fm.get("status", "").strip().strip('"').strip("'")
        others = [p for p in L.iter_md_files(proj)
                  if p.name not in (INSTRUCTION, L.PROJECT_INDEX)
                  and not L.is_teach_scaffold(L.rel_path(p))]
        expect = "learning" if others else "todo"
        if status not in ("done", "review") and status != expect:
            out.append(L.Finding("A7", L.rel_path(fm_file), 0,
                                 "status=%s 与项目内文件数不符(应为 %s)" % (status, expect)))
        if not quiet and proj.name not in listed:
            out.append(L.Finding("A7", anchor, 0, "项目 %s 未进路线" % proj.name))
    return out


def _project_status(proj: Path) -> str:
    fm_file = proj / INSTRUCTION
    if not fm_file.exists():
        return ""
    fm = L.parse_frontmatter(L.read_text(fm_file))
    return (fm or {}).get("status", "").strip().strip('"').strip("'")


def check_index_stats() -> list[L.Finding]:
    """A9(项目口径):项目统计行的篇数/状态/覆盖须与实物一致;根汇总行的 N/M 须与盘上一致。"""
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
    root_index = L.VAULT_ROOT / L.ROOT_INDEX
    if root_index.exists():
        rel = L.rel_path(root_index)
        m = ROOT_STATS.search(_head(L.read_text(root_index)))
        if not m:
            out.append(L.Finding("A9", rel, 0, "缺汇总行(`> 全库知识 N 篇 · 项目 M 个`)"))
            return out
        if int(m.group(1)) != total:
            out.append(L.Finding("A9", rel, 0, "汇总行知识 %s 篇与各项目之和 %d 不符" % (m.group(1), total)))
        n_projects = len(L.project_dirs(L.VAULT_ROOT))
        if m.group(2) is None:
            out.append(L.Finding("A9", rel, 0, "汇总行缺「项目 M 个」(格式 `> 全库知识 N 篇 · 项目 M 个`)"))
        elif int(m.group(2)) != n_projects:
            out.append(L.Finding("A9", rel, 0, "汇总行项目 %s 个与盘上项目 %d 不符" % (m.group(2), n_projects)))
    return out
