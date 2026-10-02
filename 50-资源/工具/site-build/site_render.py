#!/usr/bin/env python3
"""0-Note 在线阅读站 · 整页渲染(把扫描结果 + markdown + 样式 + 交互拼成 HTML)。

DOM 形状照 `site_dom.CONTRACT`(唯一真源);条目准备与站内链接改写在 `site_links.py`。
对外接口:`render_page(entries, *, mode, generated_at, rev) -> str`(整页 HTML 字符串)。
"""
from __future__ import annotations

import html as H
import json
import posixpath
import re
import sys
from pathlib import Path

import site_css
import site_js
from site_css_prose import PROSE
from site_md import render_md
from site_links import entry_anchor, fix_md_links, known_map, lesson_ctx, prepare
from site_parts import ICON, chips, overview, project_grid, slug_of, toc

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT_ROOT = Path(__file__).resolve().parents[3]
TYPE_LABEL = {"course": "课程", "know": "知识", "project": "项目", "log": "记录", "index": "索引", "template": "模板"}
TEXT_CAP = 600
SITE_TITLE = "0-Note · 读书页"

__all__ = ["render_page", "entry_anchor"]


def _card(e: dict, known: dict, ctx: dict) -> str:
    parts = ['<article class="card" id="%s" data-kind="%s" data-status="%s">' % (e["anchor"], e["kind_of"], e["status"])]
    parts.append('<div class="card-head"><h3 class="card-title"><a href="%s">%s</a></h3>'
                 '<div class="card-meta"><span class="badge" data-type="%s" data-status="%s">%s</span>'
                 '<span class="when">%s</span></div></div>'
                 % (H.escape(e["href"], quote=True), H.escape(e["show_title"]), e["type_badge"], e["status"],
                    TYPE_LABEL[e["type_badge"]], H.escape(e.get("date") or "")))
    win = (e.get("win") or "").strip()
    if e["sum"] != win:
        parts.append('<p class="card-sum">%s</p>' % H.escape(e["sum"]))
    if win:
        parts.append('<p class="card-win">%s</p>' % H.escape(win))
    if e.get("related"):
        rels = []
        for r in e["related"]:
            a = known.get(r) or known.get(slug_of(r))
            rels.append('<a href="#%s">%s</a>' % (a, H.escape(r)) if a else H.escape(r))
        parts.append('<div class="card-rel">相关:%s</div>' % " · ".join(rels))
    if e.get("body"):
        frag = render_md(e["body"], known)
        frag = fix_md_links(frag, known, base_dir=posixpath.dirname(e["path"]), anchor=e["anchor"],
                            lesson_paths=ctx["lesson_paths"], lesson_by_code=ctx["lesson_by_code"])
        parts.append('<div class="card-body">%s</div>' % frag)
    parts.append("</article>")
    return "".join(parts)


def _order() -> list[str]:
    """节的顺序照库里既有的根索引项目清单(spec 5.6);读不到就按名字排。"""
    try:
        text = (VAULT_ROOT / "00-索引" / "00-索引.md").read_text(encoding="utf-8")
    except OSError:
        return []
    seen: list[str] = []
    for m in re.finditer(r"(?:10-项目|50-资源|90-模板)/([^/\s)\]]+)/", text):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def _sections(items: list[dict]) -> list[tuple[str, str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for e in items:
        groups.setdefault(e["section"], []).append(e)
    seq = _order()
    names = sorted(groups, key=lambda n: (seq.index(n) if n in seq else len(seq) + (n == "90-模板"), n))
    return [(n, slug_of(n) or "root", groups[n]) for n in names]


def _index_json(items: list[dict]) -> str:
    idx = [{"title": e["show_title"], "summary": e["sum"], "text": e["text"][:TEXT_CAP],
            "kind": e["kind_of"], "status": e["status"], "anchor": e["anchor"], "href": e["href"]} for e in items]
    return json.dumps(idx, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _section_html(name: str, slug: str, items: list[dict], *, known: dict, ctx: dict) -> str:
    return ('<section class="sec" id="sec-%s"><h2 class="sec-title">%s <span class="muted">%d 条</span></h2>'
            '<div class="cards">%s</div></section>'
            % (slug, H.escape(name), len(items), "".join(_card(e, known, ctx) for e in items)))


def render_page(entries: list[dict], *, mode: str, generated_at: str, rev: str) -> str:
    items = prepare(entries)
    known = known_map(items)
    secs = _sections(items)
    lp, lbc = lesson_ctx()
    ctx = {"lesson_paths": lp, "lesson_by_code": lbc}
    label = "对外" if mode == "public" else "全库"
    head = (
        '<!DOCTYPE html><html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<title>%s(%s)</title><meta name="description" content="0-Note %s阅读页:%d 条,来自已入库的笔记与课程。">'
        '<script>%s</script><style>%s%s</style></head><body>'
        % (SITE_TITLE, label, label, len(items), site_js.BOOT, site_css.CSS, PROSE)
    )
    bar = (
        '<a class="skip" href="#main">跳到正文</a><header class="bar"><div class="bar-inner">'
        '<a class="brand" href="#main">0-Note <small>%s读书页</small></a>'
        '<div class="search-wrap"><span class="search-ico">%s</span>'
        '<label class="sr" for="q">搜索标题与正文</label>'
        '<input class="search" id="q" type="search" placeholder="搜索标题、摘要、正文…" autocomplete="off">'
        '<button class="search-clear" id="clear" aria-label="清空搜索">%s</button>'
        '<span class="search-count" id="count" aria-live="polite"></span></div>'
        '<span class="spacer"></span>'
        '<button class="icon-btn" id="theme" aria-label="切换明暗主题" aria-pressed="false">%s</button>'
        '<button class="icon-btn menu-btn" id="menu" aria-label="打开目录" aria-expanded="false">%s</button>'
        '</div></header>'
        % (label, ICON["search"], ICON["close"], ICON["theme"], ICON["menu"])
    )
    content = (
        '%s%s%s%s<p class="no-result" id="empty" hidden>没有匹配的条目。<button class="link-btn" id="clear2" '
        'aria-label="清空筛选">清空筛选</button></p>'
        % (overview(items, generated_at=generated_at, rev=rev, title=label),
           chips(items), project_grid(secs), "".join(_section_html(*s, known=known, ctx=ctx) for s in secs))
    )
    tail = (
        '<div class="side-mask"></div><button class="to-top" id="toTop" aria-label="回到顶部">%s</button>'
        '<footer class="foot">生成物 · 数据源 <code>git ls-files</code> · %s读书页 %d 条 · 生成于 %s</footer>'
        '<script>window.__INDEX__=%s;</script><script>%s</script></body></html>'
        % (ICON["up"], label, len(items), H.escape(generated_at), _index_json(items), site_js.JS)
    )
    layout = '<main id="main"><div class="layout">%s<div class="content">%s</div></div></main>' % (toc(secs), content)
    return head + bar + layout + tail


if __name__ == "__main__":
    import site_scan
    m = sys.argv[1] if len(sys.argv) > 1 else "public"
    page = render_page(site_scan.scan(m), mode=m, generated_at="dry-run", rev="dry-run")
    print("mode=%s 字符 %d 卡片 %d 外部资源 %d"
          % (m, len(page), page.count('class="card"'), page.count("<script src=") + page.count('<link rel="stylesheet"')))
