#!/usr/bin/env python3
"""0-Note 在线阅读站 · 页面骨架(把扫描器 / markdown / 样式 / 交互接起来)。

DOM/属性契约的唯一真源是 `site_dom.CONTRACT`:页面结构、类名、必填属性、
无障碍名逐字照它;它没写的(项目卡状态徽章、笔记正文容器 `.card-body`)按
设计稿 §5 补。对本模块的硬要求(漏一项就坏页面):

- `<head>` 内联 `site_js.BOOT`,否则深色系统用户首屏白闪;
- 索引 JSON 用 `json.dumps(..., ensure_ascii=False).replace("<", "\\u003c")`,
  否则任一条目含 `</script>`(课 HTML 里就有)会让整个脚本 SyntaxError;
- 页内零外部资源(`<link rel=stylesheet>` / `<script src=` / `@import`)。

对外接口:`render_page(entries, *, mode, generated_at, rev) -> str`,
以及给 Task 5 用的 `entry_anchor` / `entry_href`(自 `site_render_lib` 转出)。
"""
from __future__ import annotations

import json

import site_render_lib as L
from site_css import CSS
from site_js import BOOT, JS

entry_anchor = L.entry_anchor
entry_href = L.entry_href
esc = L.esc


def _svg(body: str) -> str:
    return ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" fill="none"'
            ' stroke="currentColor" stroke-width="2" stroke-linecap="round"'
            ' stroke-linejoin="round">%s</svg>' % body)


ICO_SEARCH = _svg('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>')
ICO_X = _svg('<path d="M6 6l12 12M18 6L6 18"/>')
ICO_MENU = _svg('<path d="M4 7h16M4 12h16M4 17h16"/>')
ICO_THEME = _svg('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>')
ICO_UP = _svg('<path d="M12 19V5M5 12l7-7 7 7"/>')


def _bar() -> str:
    return ('<header class="bar"><div class="bar-inner">'
            '<a class="brand" href="#main">0-Note <small>读书页</small></a>'
            '<div class="search-wrap"><span class="search-ico">%s</span>'
            '<label class="sr" for="q">搜索条目</label>'
            '<input class="search" id="q" type="search" autocomplete="off"'
            ' placeholder="搜索标题、摘要与正文">'
            '<button class="search-clear" id="clear" type="button" aria-label="清空搜索">%s'
            '</button><span class="search-count" id="count" aria-live="polite"></span></div>'
            '<span class="spacer"></span>'
            '<button class="icon-btn" id="theme" type="button" aria-label="切换明暗主题"'
            ' aria-pressed="false">%s</button>'
            '<button class="icon-btn menu-btn" id="menu" type="button" aria-label="打开目录"'
            ' aria-expanded="false">%s</button></div></header>'
            % (ICO_SEARCH, ICO_X, ICO_THEME, ICO_MENU))


def _overview(entries, groups, generated_at, rev, ctx) -> str:
    lessons = sum(1 for e in entries if e["kind"] == "lesson")
    parts = ["<span>条目 <b>%d</b></span>" % len(entries),
             "<span>项目 <b>%d</b></span>" % len(groups),
             "<span>课程 <b>%d</b></span>" % lessons]
    recent = L.recent_updates(entries)
    if recent:
        links = ['<a href="#%s">%s</a> <small>%s</small>'
                 % (esc(L.entry_anchor(ctx["by_path"][p])),
                    esc(L.display_title(ctx["by_path"][p])), esc(d)) for p, d in recent]
        parts.append("<span>最近更新 %s</span>" % " · ".join(links))
    parts.append("<span>生成 <b>%s</b></span>" % esc(generated_at))
    parts.append("<span>来源 <b>%s</b></span>" % esc(rev[:8] if rev else "本地"))
    return '<div class="overview">%s</div>' % "".join(parts)


def _filters(entries) -> str:
    chips = [(k, L.KIND_CN[k], sum(1 for e in entries if L.card_kind(e) == k))
             for k in ("course", "know", "project")]
    chips += [(s, L.STATE_CN[s], sum(1 for e in entries if L.norm_status(e["status"]) == s))
              for s in L.STATES]
    out = ['<div class="filters"><span class="lbl">筛选</span>']
    for value, label, n in chips:
        group = "kind" if value in L.KIND_CN else "status"
        out.append('<button class="chip" type="button" data-group="%s" data-value="%s"'
                   ' aria-pressed="false">%s <span class="n">%d</span></button>'
                   % (group, value, label, n))
    out.append("</div>")
    return "".join(out)


def _toc(groups, status) -> str:
    out = ['<nav class="side" aria-label="目录"><ul class="toc">']
    for name, es in groups.items():
        out.append('<li><a href="#sec-%s"><span class="dot" data-status="%s"'
                   ' aria-hidden="true"></span>%s<span class="n">%d</span></a></li>'
                   % (esc(L.project_slug(name)), L.norm_status(status.get(name, "")),
                      esc(name), len(es)))
    out.append("</ul></nav>")
    return "".join(out)


def _section(name, es, ctx) -> str:
    return ('<section class="sec" id="sec-%s"><h2 class="sec-title">%s'
            ' <span class="muted">%d 条</span></h2><div class="cards">%s</div></section>'
            % (esc(L.project_slug(name)), esc(name), len(es),
               "".join(L.card(e, ctx) for e in es)))


def page_title(mode: str) -> str:
    return "0-Note · 对外精选" if mode == "public" else "0-Note · 全库"


def render_page(entries: list[dict], *, mode: str, generated_at: str, rev: str) -> str:
    ctx = L.build_ctx(entries)
    order, status = L.section_order(entries)
    groups: dict[str, list] = {s: [] for s in order}
    for e in entries:
        groups.setdefault(e["section"], []).append(e)
    ctx["ids"] |= {"sec-" + L.project_slug(s) for s in groups}
    index = L.index_items(entries, ctx)
    lessons = sum(1 for e in entries if e["kind"] == "lesson")
    desc = ("0-Note 在线阅读站:%d 条条目(39 课 + 知识笔记),支持搜索、筛选与明暗主题。"
            % len(entries)) if mode == "public" else \
        "0-Note 全库离线页:%d 条条目,含脚手架与记录。" % len(entries)
    h = ['<!DOCTYPE html>', '<html lang="zh-CN" data-theme="light">', "<head>",
         '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         "<title>%s</title>" % esc(page_title(mode)),
         '<meta name="description" content="%s">' % esc(desc),
         "<style>%s</style>" % CSS,
         "<script>%s</script>" % BOOT,
         "</head>", "<body>",
         '<a class="skip" href="#main">跳到正文</a>', _bar(),
         '<main id="main"><div class="layout">', _toc(groups, status),
         '<div class="content">', _overview(entries, groups, generated_at, rev, ctx),
         _filters(entries)]
    h.append('<div class="proj-grid">%s</div>'
             % "".join(L.project_card(s, es, status.get(s, "")) for s, es in groups.items()))
    h += [_section(s, es, ctx) for s, es in groups.items()]
    h.append('<p class="no-result" id="empty" hidden><button class="link-btn" id="clear2"'
             ' type="button" aria-label="清空搜索与筛选">没有匹配的条目,换个词试试</button></p>')
    h += ["</div></div></main>",
          '<button class="to-top" id="toTop" type="button" aria-label="返回顶部">%s</button>' % ICO_UP,
          '<div class="side-mask"></div>',
          '<footer class="foot">0-Note 读书页 · 由 50-资源/工具/site-build 生成 · '
          '%d 条 · %d 课 · 生成于 %s · 源 %s</footer>'
          % (len(entries), lessons, esc(generated_at), esc(rev[:8] if rev else "本地")),
          "<script>window.__INDEX__ = %s</script>" % _json(index),
          "<script>%s</script>" % JS, "</body>", "</html>"]
    return "\n".join(h)


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
