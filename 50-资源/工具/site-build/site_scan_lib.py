#!/usr/bin/env python3
"""site_scan 的纯文本工具:slug 化、frontmatter 解析、摘要抽取、行内清洗。

只做 字符串 -> 字符串/结构,不碰文件系统;与 site_scan 分开以便各自守住 200 行。
"""
from __future__ import annotations

import re

SLUG_REPLACE = "! ,()（）"
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
H1_PAT = re.compile(r"^#\s+(.+?)\s*$", re.M)
BULLET = re.compile(r"^[-*+]\s")          # 只有 `- ` 才算列表,`**粗**` 不算
# 有序列表:允许 `1.` 后直接跟中文(库内有 `1.老爸的` 这种写法,要当列表行跳过)
ORDERED = re.compile(r"^\d+[.)](?:\s|(?=[\u4e00-\u9fff]))")
# 兜底摘要要剥掉的行首块级标记:`>` 引用 / `- ` `* ` `+ ` 列表 / `1.` `1)` 有序
BLOCK_MARKER = re.compile(r"^(?:>\s*|[-*+]\s+|\d+[.)](?:\s+|(?=[\u4e00-\u9fff])))+")
KV = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
TABLE_SEP = re.compile(r"^\|[\s:|-]+\|$")
HTML_BLOCK = re.compile(r"<(?:p|blockquote)>(.*?)</(?:p|blockquote)>", re.S)

SUMMARY_LIMIT = 120


def slugify(name: str) -> str:
    """文件名 -> 锚点 slug:`!`/空格/`,`/`(`/`)` 换成 `-`,其余(含中文与 `x<n>-` 前缀)保留。"""
    for ch in SLUG_REPLACE:
        name = name.replace(ch, "-")
    return re.sub(r"-{2,}", "-", name).strip("-") or "item"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """返回 (frontmatter, 正文);没有 frontmatter 时 ({}, 原文)。

    `tags` -> list[str](支持 `[a, b]` 与 `- a` 两种写法);
    `related` -> list[str](取 `[[x|y]]` 的 y、`[[x]]` 的 x,即显示文字);其余键 -> str。
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    body = text[end + 4:]
    body = body[1:] if body.startswith("\n") else body
    raw: dict[str, list[str]] = {}
    key = ""
    for line in text[3:end].splitlines():
        m = KV.match(line)
        if m:
            key = m.group(1)
            raw.setdefault(key, [])
            if m.group(2).strip():
                raw[key].append(m.group(2).strip())
        elif key and line.lstrip().startswith("- "):
            raw[key].append(line.lstrip()[2:].strip())
    fm: dict = {}
    for k, vals in raw.items():
        joined = " ".join(vals).strip().strip('"')
        if k == "tags":
            fm[k] = _tags(vals)
        elif k == "related":
            fm[k] = [w.split("|", 1)[1].strip() if "|" in w else w.strip()
                     for w in WIKILINK.findall(joined)]
        else:
            fm[k] = joined
    return fm, body


def _tags(vals: list[str]) -> list[str]:
    if len(vals) == 1 and vals[0].startswith("["):
        parts = vals[0].strip().strip("[]").split(",")
    else:
        parts = vals
    return [p.strip().strip("\"'") for p in parts if p.strip()]


def first_paragraph(md: str) -> str:
    """正文首个非空段落(跳过标题、列表、引用、表格、代码围栏),已去行内标记。"""
    para: list[str] = []
    fence = False
    for raw in md.splitlines():
        s = raw.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            if para:
                break
            continue
        if fence or not s:
            if para:
                break
            continue
        if _skip_line(s):
            if para:
                break
            continue
        para.append(s)
    return clean_inline(" ".join(para))


def _skip_line(s: str) -> bool:
    """标题 / 列表 / 引用 / 表格 / HTML / 分隔线 —— 都不是散文段落。"""
    return bool(BULLET.match(s) or ORDERED.match(s)) or s.startswith(
        ("#", ">", "|", "<", "---", "***", "==="))


def first_content(body: str) -> str:
    """兜底摘要:正文第一条有文字的行(列表 / 引用 / 表格也算),已清洗。

    表格跳过表头与其后的分隔行,取首个数据行;单元格用 ` / ` 连接。
    """
    lines = body.splitlines()
    fence = False
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if fence or not s or s.startswith(("#", "---", "===")):
            continue
        if s.startswith("|"):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if TABLE_SEP.match(nxt) or TABLE_SEP.match(s):
                continue
            cells = [c.strip() for c in s.strip("|").split("|") if c.strip()]
            return clean_inline(" / ".join(cells))
        return clean_inline(BLOCK_MARKER.sub("", s))
    return ""


def h1(body: str) -> str:
    """正文首个 H1 的纯文字;没有则空串。"""
    m = H1_PAT.search(body)
    return clean_inline(m.group(1)) if m else ""


def clean_inline(s: str) -> str:
    """去掉行内 markdown:图片/链接取文字、双链取显示名、代码与强调去壳、裸 HTML 去标签,

    并剥掉行首块级标记(`>` / `- ` / `1. `),结果必是单行纯文本。
    """
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = WIKILINK.sub(lambda m: m.group(1).split("|")[-1], s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)     # 裸 HTML 标签(如 `<sub>注:…</sub>`)
    s = s.replace("<", " ")            # 剥完标签后残留的孤立 `<`(如 shell 里的 `<<`)
    # 行首块级标记再剥一道:放在强调去壳之后,才能看到 `**1. 加信息**` 里的 `1. `
    s = BLOCK_MARKER.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def html_text(html: str) -> str:
    """HTML -> 单行纯文本(去标签、压空白)。"""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def html_paragraph(text: str) -> str:
    """`<h1>` 之后第一个 `<p>` / `<blockquote>` 的纯文本;没有则空串。"""
    tail = text.split("</h1>", 1)
    if len(tail) < 2:
        return ""
    for block in HTML_BLOCK.findall(tail[1]):
        plain = html_text(block)
        if plain:
            return plain
    return ""


def clip(text: str, limit: int = SUMMARY_LIMIT) -> str:
    """超长摘要截断到 limit 字,末尾加省略号。"""
    return text if len(text) <= limit else text[:limit].rstrip() + "…"
