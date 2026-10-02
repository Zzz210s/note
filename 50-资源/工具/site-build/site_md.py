#!/usr/bin/env python3
"""0-Note 在线阅读站 · 极简 markdown -> HTML。

只做站点真会用到的语法:标题 / 段落 / 有序无序列表 / 表格 / 围栏代码 / 行内代码 /
引用 / 粗斜体 / 链接 / Obsidian 双链 / 分隔线。图片、脚注、任务列表、HTML 透传都不做
(库里的笔记含 `<sub>` 这类内联 HTML,透传是安全风险,一律转义)。

安全与顺序:先剥代码(围栏整块、行内 span 都换成占位符,不参与语法解析),再整体转义
`<` `>` `&`,再做行内(粗体 -> 斜体 -> 链接 -> 双链),最后放回代码 —— 所以代码里的
`#` / `<b>` 既不会被当标题,也不会变成活标签。占位符用索引 token(不照搬 strip_code
的等长空格:这里没有行列位置消费者,token 更不易被 markdown 误认)。

对外接口:`render_md(md: str, known=None) -> str`(HTML 片段)。`known` 是
「条目名/文件名主干 -> 条目 slug」的映射,用于双链;默认惰性取自 `site_scan.scan("all")`,
目标不存在就退化成纯文字。站内正文只有一个 h1(渲染骨架给),故源文 `#` 降为 `h2`。
"""
from __future__ import annotations

import re
import sys

from site_scan_lib import parse_frontmatter, slugify

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BPH = re.compile(r"^\x00B(\d+)\x00$")          # 围栏代码块占位
CPH = re.compile(r"\x00C(\d+)\x00")            # 行内代码占位
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`([^`]+)`")
HR = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
ULIST = re.compile(r"^\s*[-*+]\s+(.*)$")
OLIST = re.compile(r"^\s*\d+[.)]\s+(.*)$")
QUOTE = re.compile(r"^\s*>\s?(.*)$")
TROW = re.compile(r"^\s*\|(.+)\|\s*$")
TSEP = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
# 链接 URL 有两种写法:`[x](url)` 与 `[x](<带空格的 url>)`(转义后成了 `&lt;..&gt;`)
LINK = re.compile(r"\[([^\]]+)\]\((?:&lt;([^)]*?)&gt;|([^)\s]+))\)")
WIKILINK = re.compile(r"\[\[([^\[\]]+)\]\]")

_KNOWN: dict[str, str] | None = None


def esc(s: str) -> str:
    """HTML 转义三种危险字符(先 `&` 再 `<` `>`)。"""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _default_known() -> dict[str, str]:
    """真库的「名字 -> 条目 slug」映射:文件名主干 / slug / 页面标题都索引。"""
    global _KNOWN
    if _KNOWN is None:
        import site_scan  # 惰性:避免模块加载即扫全库
        m: dict[str, str] = {}
        for e in site_scan.scan("all"):
            stem = re.sub(r"\.(?:md|html)$", "", e["path"].rsplit("/", 1)[-1])
            for key in (stem, slugify(stem), e["slug"], e["title"], slugify(e["title"])):
                m.setdefault(key, e["slug"])
        _KNOWN = m
    return _KNOWN


def _store_block(blocks: list[str], buf: list[str]) -> str:
    blocks.append("<pre><code>%s</code></pre>" % esc("\n".join(buf)))
    return "\x00B%d\x00" % (len(blocks) - 1)


def _store_inline(inlines: list[str], code: str) -> str:
    inlines.append("<code>%s</code>" % esc(code))
    return "\x00C%d\x00" % (len(inlines) - 1)


def _protect(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """剥代码:围栏 -> 块占位(整块 HTML 存 blocks),行内代码 -> 行内占位。"""
    blocks: list[str] = []
    inlines: list[str] = []
    out: list[str] = []
    fence: str | None = None
    buf: list[str] = []
    for raw in lines:
        s = raw.rstrip()
        if fence is not None:
            if s.strip().startswith(fence):
                out.append(_store_block(blocks, buf))
                fence, buf = None, []
            else:
                buf.append(s)
            continue
        m = FENCE.match(s)
        if m:
            fence, buf = m.group(1)[:3], []
            continue
        out.append(INLINE_CODE.sub(lambda mm: _store_inline(inlines, mm.group(1)), s))
    if fence is not None:                     # 未闭合围栏:当代码处理,不吞内容
        out.append(_store_block(blocks, buf))
    return out, blocks, inlines


def _wikilink(inner: str, known: dict[str, str]) -> str:
    """双链 -> 站内锚点;目标不在库里就退化成显示文字。"""
    target, _, label = inner.partition("|")
    target = target.strip()
    label = label.strip() or target.rsplit("/", 1)[-1]
    name = target.rsplit("/", 1)[-1]
    slug = known.get(target) or known.get(name) or known.get(slugify(name))
    return '<a class="wl" href="#%s">%s</a>' % (esc(slug), label) if slug else label


def _inline(s: str, known: dict[str, str]) -> str:
    """行内:转义 -> 粗体 -> 斜体 -> 链接 -> 双链(代码占位符不受影响)。"""
    s = esc(s)
    s = BOLD.sub(r"<strong>\1</strong>", s)
    s = ITALIC.sub(r"<em>\1</em>", s)
    s = LINK.sub(lambda m: '<a href="%s">%s</a>' % (
        m.group(2) if m.group(2) is not None else m.group(3), m.group(1)), s)
    return WIKILINK.sub(lambda m: _wikilink(m.group(1), known), s)


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _table(lines: list[str], i: int, out: list[str], known: dict[str, str]) -> int:
    head = _cells(lines[i])
    i += 2                                     # 跳过表头与分隔行
    rows = []
    while i < len(lines) and lines[i].strip() and TROW.match(lines[i].strip()):
        rows.append(_cells(lines[i]))
        i += 1
    th = "".join("<th>%s</th>" % _inline(c, known) for c in head)
    tb = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c, known) for c in r)
                for r in rows)
    out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, tb))
    return i


def render_md(md: str, known: dict[str, str] | None = None) -> str:
    """markdown -> HTML 片段。`known` 见模块 docstring。"""
    _, body = parse_frontmatter(md)
    lines, blocks, inlines = _protect(body.splitlines())
    known = _default_known() if known is None else known
    out: list[str] = []
    para: list[str] = []

    def flush() -> None:
        if para:
            out.append("<p>%s</p>" % _inline(" ".join(para), known))
            para.clear()

    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            flush(); i += 1; continue
        if BPH.match(lines[i]):
            flush(); out.append(blocks[int(BPH.match(lines[i]).group(1))]); i += 1; continue
        if HR.match(s):
            flush(); out.append("<hr>"); i += 1; continue
        h = HEADING.match(s)
        if h:
            flush()
            lv = min(len(h.group(1)) + 1, 6)
            out.append("<h%d>%s</h%d>" % (lv, _inline(h.group(2), known), lv))
            i += 1; continue
        if TROW.match(s) and i + 1 < n and TSEP.match(lines[i + 1]):
            flush(); i = _table(lines, i, out, known); continue
        if QUOTE.match(s):
            flush(); buf = []
            while i < n and QUOTE.match(lines[i].strip()):
                buf.append(QUOTE.match(lines[i].strip()).group(1)); i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % _inline(" ".join(buf), known))
            continue
        if ULIST.match(s) or OLIST.match(s):
            flush()
            pat, tag = (ULIST, "ul") if ULIST.match(s) else (OLIST, "ol")
            items = []
            while i < n and pat.match(lines[i].strip()):
                items.append("<li>%s</li>" % _inline(pat.match(lines[i].strip()).group(1), known))
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join(items), tag))
            continue
        para.append(s)
        i += 1
    flush()
    return CPH.sub(lambda m: inlines[int(m.group(1))], "".join(out))
