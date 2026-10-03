#!/usr/bin/env python3
"""0-Note 在线阅读站 · 整页渲染(工作台骨架 + 欢迎页空态)。

DOM 形状照 `site_dom.CONTRACT`(唯一真源):`body.work` 是固定外壳(标题栏 / 活动栏 /
侧栏两棵树 / 两组编辑区 / 状态栏);欢迎页是「该组无标签时的空态」,不占标签位,里面是
原有的总览 / 项目卡网格 / 条目流 / 筛选 / 无结果提示。笔记正文预置在 `.note-body[data-key]`
(默认 `hidden`,JS 按 key 显隐),课只放 `iframe.lesson-frame`(初始 `about:blank`,
真路径走树项 `data-href`)。条目准备与站内链接改写见 `site_links.py`,两棵树 / 状态栏见
`site_parts.py`,交互由 `site_work_js`(标签 / 侧栏 / 分屏)+ `site_work_palette`(快速打开 / 命令面板)+ `site_js`(欢迎页筛选 / 搜索)消费。对外接口:
`render_page(entries, *, mode, generated_at, rev) -> str`(整页 HTML 字符串)。
"""
from __future__ import annotations

import html as H
import json
import posixpath
import re
import sys
from pathlib import Path

import site_css
import site_counts
import site_js
import site_search
import site_work_css
import site_work_js
import site_work_palette
from site_css_prose import PROSE
from site_md import render_md
from site_links import fix_md_links, known_map, lesson_ctx, prepare
from site_parts import (ICON, KIND_LABEL, chips, course_tree, note_tree, overview,
                        project_grid, slug_of, statusbar)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT_ROOT = Path(__file__).resolve().parents[3]
TYPE_LABEL = {"course": "课程", "know": "知识", "project": "项目", "log": "记录", "index": "索引", "template": "模板"}
SITE_TITLE = "0-Note · 工作台"

__all__ = ["render_page"]


def _card(e: dict, known: dict) -> str:
    """欢迎页条目卡:只放元信息(正文在编辑区的 `.note-body`,不在这里重复渲染)。"""
    parts = ['<article class="card" id="%s" data-kind="%s" data-status="%s">'
             % (H.escape(e["anchor"], quote=True), e["kind_of"], e["status"])]
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
    idx = site_search.build_index(items)
    return json.dumps(idx, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _section_html(name: str, slug: str, items: list[dict], *, known: dict) -> str:
    return ('<section class="sec" id="sec-%s"><h2 class="sec-title">%s <span class="muted">%d 条</span></h2>'
            '<div class="cards">%s</div></section>'
            % (slug, H.escape(name), len(items), "".join(_card(e, known) for e in items)))


def _welcome(items: list[dict], sections: list[tuple], known: dict, *, generated_at: str, rev: str, label: str) -> str:
    """欢迎页内容:总览 + 筛选 chips + 命中数 + 项目卡网格 + 条目流 + 无结果提示。"""
    body = (overview(items, generated_at=generated_at, rev=rev, title=label) + chips(items)
            + '<span class="search-count" id="count" aria-live="polite"></span>'
            + project_grid(sections)
            + "".join(_section_html(name, slug, group, known=known) for name, slug, group in sections)
            + '<p class="no-result" id="empty" hidden>没有匹配的条目。'
              '<button class="link-btn" id="clear2" aria-label="清空筛选">清空筛选</button></p>')
    return body   # 外层 .group-body 由 _group 包(此处再包会变成两层滚动容器)


def _note_bodies(items: list[dict], known: dict, ctx: dict) -> str:
    """每篇笔记的正文预置成一个 `.note-body[data-key]`(默认 hidden,JS 按 key 显隐)。"""
    out = []
    for e in items:
        if e["kind"] != "note" or not e.get("body"):
            continue
        frag = render_md(e["body"], known)
        frag = fix_md_links(frag, known, base_dir=posixpath.dirname(e["path"]), anchor=e["anchor"],
                            lesson_paths=ctx["lesson_paths"], lesson_by_code=ctx["lesson_by_code"])
        out.append('<div class="note-body card-body" data-key="%s" hidden>%s</div>'
                   % (H.escape(e["anchor"], quote=True), frag))
    return "".join(out)


def _group(g: int, welcome: str, notes: str, lesson_href: str, *, open_: bool) -> str:
    """一个编辑组:自己的标签栏 + welcome / note / lesson 三个面板。"""
    h = "" if open_ else " hidden"
    return ('<section class="group" data-group="%d"%s>'
            '<div class="group-tabs" role="tablist" aria-label="编辑组 %d 标签"%s></div>'
            '<div class="group-body" data-kind="welcome"%s>%s</div>'
            '<div class="group-body" data-kind="note" hidden>%s</div>'
            '<div class="group-body" data-kind="lesson" hidden>'
            '<iframe class="lesson-frame" title="课程(内嵌文档)" src="about:blank" data-src="%s"></iframe>'
            '</div></section>'
            % (g, h, g, h, h, welcome, notes, lesson_href))


def render_page(entries: list[dict], *, mode: str, generated_at: str, rev: str) -> str:
    items = prepare(entries)
    known = known_map(items)
    secs = _sections(items)
    lp, lbc = lesson_ctx()
    ctx = {"lesson_paths": lp, "lesson_by_code": lbc}
    label = "对外" if mode == "public" else "全库"
    lesson_href = next((e["href"] for e in items if e["kind"] == "lesson"), "")
    kinds = [k for k in ("course", "know", "project") if any(e["kind_of"] == k for e in items)]

    head = (
        '<!DOCTYPE html><html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<title>%s(%s)</title><meta name="description" content="0-Note %s工作台:%d 条,来自已入库的笔记与课程。">'
        '<script>%s</script><style>%s%s%s</style></head><body class="work">'
        % (SITE_TITLE, label, label, len(items), site_work_js.WORK_BOOT, site_css.CSS, PROSE, site_work_css.WORK_CSS)
    )
    titlebar = (
        '<a class="skip" href="#editor">跳到编辑区</a><header class="titlebar">'
        '<span class="tb-title">0-Note <small>%s工作台</small></span><div class="tb-actions">'
        '<button class="icon-btn" id="theme" aria-label="切换明暗主题" aria-pressed="false">%s</button>'
        '<button class="icon-btn menu-btn" id="menu" aria-label="开关侧栏" aria-expanded="true">%s</button>'
        '</div></header>' % (label, ICON["theme"], ICON["menu"])
    )
    activity = (
        '<nav class="activity" aria-label="活动栏">'
        '<button class="act" data-panel="files" aria-pressed="true" aria-label="资源管理器">%s</button>'
        '<button class="act" data-panel="search" aria-pressed="false" aria-label="搜索">%s</button>'
        '<button class="act" data-panel="commands" aria-pressed="false" aria-label="命令">%s</button>'
        '<span class="act-spacer"></span>'
        '<button class="act" id="act-theme" aria-label="切换明暗主题">%s</button></nav>'
        % (ICON["files"], ICON["search"], ICON["terminal"], ICON["theme"])
    )
    side_chips = "".join('<button class="chip" data-group="kind" data-value="%s" aria-pressed="false">%s'
                         '<span class="n"></span></button>' % (k, KIND_LABEL[k]) for k in kinds)
    sidebar = (
        '<aside class="sidebar" data-open="true" data-panel="files">'
        '<div class="side-head"><input id="side-q" type="search" aria-label="筛选条目" '
        'placeholder="筛选条目…" autocomplete="off"><div class="filters"><span class="lbl">筛选:</span>%s</div></div>'
        '<div class="side-tree">%s%s</div></aside>'
        % (side_chips, course_tree(items), note_tree(items))
    )
    second = '<div class="overview"><span>第二组:把标签拖到这里,或按 Ctrl+\\ 合并</span></div>'
    editor = ('<main class="editor" id="editor"><div class="groups" data-split="false">%s%s</div></main>'
              % (_group(1, _welcome(items, secs, known, generated_at=generated_at, rev=rev, label=label),
                        _note_bodies(items, known, ctx), lesson_href, open_=True),
                 _group(2, second, "", lesson_href, open_=False)))
    tail = ('<script>window.__INDEX__=%s;</script><script>window.__COUNTS__=%s;</script>'
            '<script>%s</script><script>%s</script><script>%s</script><script>%s</script></body></html>'
            % (_index_json(items), site_counts.seed_json(entries), site_counts.COUNTS_JS,
               site_work_js.WORK_JS, site_work_palette.PALETTE_JS, site_js.JS))
    return (head + titlebar + '<div class="work-body">' + activity + sidebar + editor + '</div>'
            + statusbar(items) + '<div class="side-mask"></div>' + tail)


if __name__ == "__main__":
    import site_scan
    m = sys.argv[1] if len(sys.argv) > 1 else "public"
    page = render_page(site_scan.scan(m), mode=m, generated_at="dry-run", rev="dry-run")
    print("mode=%s 字符 %d 卡片 %d 外部资源 %d"
          % (m, len(page), page.count('class="card"'), page.count("<script src=") + page.count('<link rel="stylesheet"')))
