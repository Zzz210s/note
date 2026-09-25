#!/usr/bin/env python3
"""0-Note 巡检公共库:扫描、frontmatter 解析、链接抽取、白名单。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, NamedTuple

# 本文件位于 <仓库根>/50-资源/工具/vault-check/,故 parents[3] = 仓库根
VAULT_ROOT = Path(__file__).resolve().parents[3]

SKIP_DIRS = {".git", "node_modules", ".obsidian", ".trash", ".superpowers", "docs"}

# teach 教学工作区的协议文件/目录(2026-09-24 起):它们是教学状态(MISSION 等),不是库内笔记,
# 因此豁免 A3 孤篇 / A5-A6 元数据 / A7 项目产出计数,改由 A11 单独守完整性。
TEACH_SCAFFOLD_FILES = ("MISSION.md", "RESOURCES.md", "NOTES.md", "GLOSSARY.md")
TEACH_SCAFFOLD_DIRS = ("lessons", "reference", "assets", "learning-records")


def is_teach_scaffold(rel: str) -> bool:
    """rel 是仓库根相对路径(posix)。只认 `10-项目/` 下的教学工作区。"""
    if not rel.startswith("10-项目/"):
        return False
    parts = rel.split("/")
    if parts[-1] in TEACH_SCAFFOLD_FILES:
        return True
    return any(d in parts[:-1] for d in TEACH_SCAFFOLD_DIRS)

# 项目引导结构(2026-09-25 起):知识住进 `10-项目/<项目>/20-知识/`,由该项目 `00-索引.md` 收录。
PROJECT_ROOT = "10-项目"
PROJECT_INDEX = "00-索引.md"
KNOWLEDGE_DIR = "20-知识"
CONTAINERS = ("10-项目/!名词解释", "10-项目/!系统与工具")


def is_container(rel: str) -> bool:
    """rel 是否属于两个容器(`!名词解释` / `!系统与工具`)或其内部文件。

    按目录前缀匹配:裸前缀会误判 `10-项目/!系统与工具旧/x.md`。"""
    return any(rel == c or rel.startswith(c + "/") for c in CONTAINERS)


def project_knowledge_dirs(root: Path = VAULT_ROOT) -> list[tuple[str, Path]]:
    """已存在的 `10-项目/<项目>/20-知识` → [(项目名, 目录)];没有 10-项目 时为空。"""
    base = root / PROJECT_ROOT
    if not base.is_dir():
        return []
    return [(p.name, p / KNOWLEDGE_DIR) for p in sorted(base.iterdir())
            if p.is_dir() and (p / KNOWLEDGE_DIR).is_dir()]


def project_dirs(root: Path = VAULT_ROOT) -> list[Path]:
    """`10-项目/` 下的项目目录(含 `!项目说明.md` 的;`!问题追踪` 这类容器不算)。"""
    base = root / PROJECT_ROOT
    if not base.is_dir():
        return []
    return [p for p in sorted(base.iterdir()) if (p / "!项目说明.md").is_file()]


def route_sources(root: Path | None = None) -> list[Path]:
    """A7 的「路线条目来源」页:根 `00-索引.md`(若存在)+ 各项目 `00-索引.md`。

    过渡期(旧结构未拆)额外带上旧的 `00-索引/系统.md`:否则取数为空,会把每个项目
    误报成「未进路线」。旧 MOC 删除后这一项自然消失 —— 知识的新家是
    `10-项目/<项目或容器>/20-知识/`,旧 MOC 与其 `20-领域/` 覆盖目录一起退场。
    """
    root = root or VAULT_ROOT
    out: list[Path] = []
    for rel in (PROJECT_INDEX, "00-索引/系统.md"):
        p = root / rel
        if p.exists():
            out.append(p)
    base = root / PROJECT_ROOT
    if base.is_dir():
        out.extend(p / PROJECT_INDEX for p in sorted(base.iterdir())
                   if p.is_dir() and (p / PROJECT_INDEX).exists())
    return out


# A5/A6/A8 豁免:索引入口层(含根 `00-索引.md`)/ 模板层 / 问题追踪(目录前缀)+ 根级 README。
# 不能写成裸前缀 `README`,否则 `README-old.md` 会被一并豁免。
FM_EXEMPT_PREFIXES = ("00-索引/", "90-模板/", "10-项目/!问题追踪/")
FM_EXEMPT_FILES = ("README.md", "README.zh-CN.md", "00-索引.md")


def is_fm_exempt(rel: str) -> bool:
    return rel in FM_EXEMPT_FILES or rel.startswith(FM_EXEMPT_PREFIXES)


# 模板占位路径 / 语法示例 / 文档里举的例,不算断链
LINK_WHITELIST = (
    "相对路径", "链接", "网址", "url", "其他文件.md", "B.md", "目录/文件",
)
# 刻意保留的「待补坑」双链
WIKILINK_WHITELIST = ("快速排序",)

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


def md_stem_counts(root: Path = VAULT_ROOT) -> dict[str, int]:
    """每个文件名 stem 在全库出现的次数;用于判定裸双链是否唯一可解析。"""
    counts: dict[str, int] = {}
    for p in iter_md_files(root):
        counts[p.stem] = counts.get(p.stem, 0) + 1
    return counts


def moc_stats() -> list[str]:
    """每张 MOC 的「条目」数(行首为 `- [` 的行数)。"""
    lines: list[str] = []
    for m in sorted((VAULT_ROOT / "00-索引").glob("*.md")):
        n = sum(1 for ln in read_text(m).splitlines() if ln.startswith("- ["))
        lines.append("%s 条目 %d" % (m.name, n))
    return lines
