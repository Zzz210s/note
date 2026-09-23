#!/usr/bin/env python3
"""0-Note 巡检公共库:扫描、frontmatter 解析、链接抽取、白名单。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, NamedTuple

# 本文件位于 <仓库根>/30-Resources/工具/vault-check/,故 parents[3] = 仓库根
VAULT_ROOT = Path(__file__).resolve().parents[3]

SKIP_DIRS = {".git", "node_modules", ".obsidian", ".trash", ".superpowers", "docs"}

# 模板占位路径 / 语法示例 / 文档里举的例,不算断链
LINK_WHITELIST = (
    "相对路径", "链接", "网址", "url", "其他文件.md", "B.md", "目录/文件",
    "20-Areas/02-编程语言/markdown/Markdown语法.md",
    "20-Areas/03-开发工具/编辑器,编译器,IDE的区别.md",
)
# 刻意保留的「待补坑」双链
WIKILINK_WHITELIST = ("快速排序",)

ROADMAP_MOC = "00-MOC/系统.md"
ROADMAP_HEADING = "## 学习路线"

CODE_FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
LINK_RE = re.compile(r"\]\((?:<([^>]+)>|([^)\s]+))\)")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


class Finding(NamedTuple):
    stage: str   # A1..A6
    path: str    # 相对仓库根
    line: int
    detail: str


def rel_path(p: Path) -> str:
    """仓库根相对路径,统一用 / 分隔。"""
    return str(p.relative_to(VAULT_ROOT)).replace("\\", "/")


def iter_md_files(root: Path = VAULT_ROOT) -> Iterator[Path]:
    for p in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """返回 frontmatter 的顶层 key->原始值;无则 None。"""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def strip_code(text: str) -> str:
    """把围栏代码块与行内代码替换为等长空白,保持行号与列位置。"""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if CODE_FENCE.match(line):
            in_fence = not in_fence
            out.append(" " * len(line))
        elif in_fence:
            out.append(" " * len(line))
        else:
            out.append(INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line))
    return "\n".join(out)


def extract_links(text: str) -> Iterator[tuple[int, str]]:
    for i, line in enumerate(strip_code(text).splitlines(), 1):
        for m in LINK_RE.finditer(line):
            yield i, (m.group(1) or m.group(2))


def extract_wikilinks(text: str) -> Iterator[tuple[int, str]]:
    for i, line in enumerate(strip_code(text).splitlines(), 1):
        for m in WIKILINK_RE.finditer(line):
            yield i, m.group(1)


def md_stems(root: Path = VAULT_ROOT) -> set[str]:
    return {p.stem for p in iter_md_files(root)}


def roadmap_section(text: str) -> str:
    """「## 学习路线」小节文本(到下一个二级标题为止;没有则返回空串)。"""
    start = text.find(ROADMAP_HEADING)
    if start == -1:
        return ""
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def check_roadmap() -> list[Finding]:
    """A7:系统.md 学习路线与 10-Projects 双向一致,且项目 status 与产出相符。

    正向:路线里指向 ../10-Projects/ 的链接必须存在(与 A1 有重叠,保留)。
    反向:每个含 !项目说明.md 的项目目录都必须在「## 学习路线」小节里被链接。
    status:项目内除 !项目说明.md 外还有 .md(含 !实施计划.md,设计文档决策 3(c))→ learning,否则 todo。
    """
    out: list[Finding] = []
    sysmd = VAULT_ROOT / ROADMAP_MOC
    text = read_text(sysmd)
    for line, target in extract_links(text):
        bare = target.split("#")[0]
        if bare.startswith("../10-Projects/") and not (sysmd.parent / bare).resolve().exists():
            out.append(Finding("A7", ROADMAP_MOC, line, target))
    listed = [t.split("#")[0] for _, t in extract_links(roadmap_section(text))]
    for proj in sorted((VAULT_ROOT / "10-Projects").iterdir()):
        fm_file = proj / "!项目说明.md"
        if not proj.is_dir() or not fm_file.exists():
            continue
        fm = parse_frontmatter(read_text(fm_file))
        if fm is None:
            continue  # 缺 frontmatter 由 A6 报,A7 不重复报
        status = fm.get("status", "").strip().strip('"').strip("'")
        # 只有 !项目说明.md 是纯立项样板;!实施计划.md 算「项目内已有产出」——
        # 设计文档 2026-09-22-0-Note整理-design.md 决策 3(c) 给 2026-10-掌握Markdown
        # 「补 !实施计划.md,让 status=learning 有据」,所以它必须计入。
        others = [p for p in iter_md_files(proj) if p.name != "!项目说明.md"]
        expect = "learning" if others else "todo"
        if status not in ("done", "review") and status != expect:
            out.append(Finding("A7", rel_path(fm_file), 0,
                               "status=%s 与项目内文件数不符(应为 %s)" % (status, expect)))
        if not any(t.startswith("../10-Projects/%s/" % proj.name) for t in listed):
            out.append(Finding("A7", ROADMAP_MOC, 0, "项目 %s 未进学习路线" % proj.name))
    return out


def moc_stats() -> list[str]:
    """每张 MOC 的「条目」数(行首为 `- [` 的行数)。"""
    lines: list[str] = []
    for m in sorted((VAULT_ROOT / "00-MOC").glob("*.md")):
        n = sum(1 for ln in read_text(m).splitlines() if ln.startswith("- ["))
        lines.append("%s 条目 %d" % (m.name, n))
    return lines
