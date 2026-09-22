#!/usr/bin/env python3
"""0-Note 巡检公共库:扫描、frontmatter 解析、链接抽取、白名单。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, NamedTuple

# 本文件位于 <仓库根>/30-Resources/tools/vault-check/,故 parents[3] = 仓库根
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

CODE_FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
LINK_RE = re.compile(r"\]\((?:<([^>]+)>|([^)\s]+))\)")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


class Finding(NamedTuple):
    stage: str   # A1..A6
    path: str    # 相对仓库根
    line: int
    detail: str


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
