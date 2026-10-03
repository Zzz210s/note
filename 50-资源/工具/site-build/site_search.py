#!/usr/bin/env python3
"""0-Note 在线阅读站 · 搜索索引与命中片段(生成侧)。

`window.__INDEX__` 的内容由 `build_index()` 产出:每条 `{title, summary, text, kind,
status, anchor, href}` 的 `text` 是完整可搜索正文 —— 课 / 参考页读 HTML,去
`<script>` / `<style>` 与标签;笔记走 frontmatter 之后的 markdown,去标记但**保留代码
围栏正文**(课件里也有命令,搜索要能命中)。`snippet()` 返回命中位置前后各 `width` 字的
纯文本,`<mark>` 高亮由前端做。JSON 序列化(含 `.replace("<", "\\u003c")`)留在
`site_render._index_json`,此处只产出 Python 结构。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import site_links
from site_scan_lib import clean_inline, html_doc_text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT_ROOT = Path(__file__).resolve().parents[3]
FENCE_LINE = re.compile(r"^\s{0,3}(?:```|~~~).*$", re.M)
HEAD_MARK = re.compile(r"^\s{0,3}#{1,6}\s+", re.M)


def md_doc_text(body: str) -> str:
    """markdown -> 单行纯文本(去围栏 / 标题标记与行内符号,保留代码正文)。"""
    return clean_inline(HEAD_MARK.sub(" ", FENCE_LINE.sub(" ", body or "")))


def entry_text(entry: dict) -> str:
    """条目参与搜索的正文;文件读不到时退回空串(不因一条坏路径让整站构建失败)。"""
    path = entry.get("path") or ""
    if path.endswith(".html"):
        try:
            raw = (VAULT_ROOT / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return html_doc_text(raw)
    return md_doc_text(entry.get("body") or "")


def snippet(text: str, term: str, width: int = 30) -> str:
    """命中位置前后各 `width` 字的纯文本;`term` 为空或不命中返回空串,绝不越界。"""
    if not term:
        return ""
    pos = text.find(term)
    if pos < 0:
        return ""
    return text[max(0, pos - width):min(len(text), pos + len(term) + width)]


def build_index(entries: list[dict]) -> list[dict]:
    """条目清单 -> `__INDEX__` 结构;`text` 不截断(设计 §5:正文全文进索引)。"""
    idx = []
    for e in site_links.prepare(entries):
        idx.append({"title": e["show_title"], "summary": e["sum"], "text": entry_text(e),
                    "kind": e["kind_of"], "status": e["status"], "anchor": e["anchor"], "href": e["href"]})
    return idx
