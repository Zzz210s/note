#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台侧栏两区块(课程 / 笔记)的静态 HTML。

从 `site_parts.py` 拆出(守库规「每个 .py ≤ 200 行」)。侧栏是**两个独立区块**:
`section.side-sec[data-section=course|note]`,各带标题行(图标 / 名称 / 计数 / 折叠按钮 /
筛选按钮)。课程按项目分组、默认只展开第一个;笔记按项目分组(记录组标「记录」)、
分组默认全收起。**标签视图不在服务端渲染**:每个笔记项带 `data-tags`(`data-tags`
内用 `|` 分隔),前端 `site_work_filter` 按需现建 —— 同一篇笔记因此不会在页面里出现
两遍(旧实现按项目 + 按标签同时铺开,165 项 = 68 去重 + 97 重复)。

DOM 形状照 `site_dom.CONTRACT`「工作台页」;本模块不读磁盘,只吃条目 dict。
"""
from __future__ import annotations

import html as H

from site_counts import bake

# 侧栏区块图标(自足:不依赖 site_parts.ICON,免得两模块互相 import)
ICON_BOOK = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h11'
             'v16H6a2 2 0 0 0-2 2z"/><path d="M8 7h6M8 11h6"/></svg>')
ICON_NOTE = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6z"/>'
             '<path d="M15 3v4h4M9 12h6M9 16h6"/></svg>')
ICON_FILTER = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16l-6 7v6l-4 2v-8z"/></svg>'
ICON_CARET = '<svg class="icon sec-caret" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 10l5 5 5-5"/></svg>'

NOTE_BADGE = {"course": "课程", "know": "知识", "project": "项目",
              "log": "记录", "index": "索引", "template": "模板"}


def _by_section(items: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for e in items:
        groups.setdefault(e["section"], []).append(e)
    return groups


def _group_html(name: str, group: list[dict], rows: str, *, expanded: bool = False) -> str:
    return ('<li><button class="tree-group" aria-expanded="%s"><span class="t-name">%s</span>'
            '<span class="t-count">%d</span></button><ul>%s</ul></li>'
            % ("true" if expanded else "false", H.escape(name), len(group), rows))


def _course_item(e: dict, baked: dict) -> str:
    n = (baked.get(e["slug"]) or {}).get("count", 0)
    return ('<li><button class="tree-item" data-key="%s" data-kind="course" data-count="%d" '
            'data-href="%s"><span class="t-name">%s</span><span class="t-count">%d</span></button></li>'
            % (H.escape(e["slug"], True), n, H.escape(e["href"], True), H.escape(e["show_title"]), n))


def _note_item(e: dict) -> str:
    btype = "log" if e.get("is_record") else e["type_badge"]
    tags = "|".join(e.get("tags") or [])
    return ('<li><button class="tree-item" data-key="%s" data-kind="note" data-count="0" data-tags="%s">'
            '<span class="t-name">%s</span><span class="badge" data-type="%s">%s</span></button></li>'
            % (H.escape(e["slug"], True), H.escape(tags, True), H.escape(e["title"]), btype,
               H.escape(NOTE_BADGE.get(btype, btype))))


def _tree(items: list[dict], *, label: str, data_group: str, note: bool) -> str:
    """两棵树共用:按项目分组,组头默认只展开第一个(课程区块如此,笔记区块全收起)。"""
    baked = bake(items)
    parts = []
    for i, (name, group) in enumerate(sorted(_by_section(items).items(), key=lambda kv: (-len(kv[1]), kv[0]))):
        label2 = "记录" if note and all(e.get("is_record") for e in group) else name
        key = (lambda x: x["title"]) if note else (lambda x: x["show_title"])
        rows = "".join((_note_item(e) if note else _course_item(e, baked)) for e in sorted(group, key=key))
        parts.append(_group_html(label2, group, rows, expanded=(not note and i == 0)))
    return '<ul class="tree" data-group="%s" aria-label="%s">%s</ul>' % (data_group, label, "".join(parts))


def course_tree(items: list[dict]) -> str:
    """课程树:按项目分组;树项次数 = 烘焙初值(浏览器里由 JS 回填);首个分组展开。"""
    return _tree([e for e in items if e["kind"] == "lesson"], label="课程", data_group="course", note=False)


def note_tree(items: list[dict]) -> str:
    """笔记树(按项目视图):每个笔记项带 `data-tags`,标签视图由前端现建。"""
    return _tree([e for e in items if e["kind"] == "note"], label="笔记", data_group="note", note=True)


def _section(sec: str, name: str, count: int, icon: str, body: str, filter_label: str) -> str:
    """一个区块:标题行(整块折叠 + 计数 + 筛选按钮)+ 区块体。"""
    return ('<section class="side-sec" data-section="%s">'
            '<div class="sec-head">'
            '<button class="sec-toggle" type="button" aria-expanded="true" aria-controls="sec-%s-body"'
            ' aria-label="折叠或展开%s区块">%s<span class="sec-name">%s</span>'
            '<span class="sec-count">%d</span>%s</button>'
            '<button class="sec-filter" type="button" aria-pressed="false" aria-label="%s" title="%s">%s</button>'
            '</div><div class="sec-body" id="sec-%s-body">%s</div></section>'
            % (sec, sec, name, icon, name, count, ICON_CARET,
               filter_label, filter_label, ICON_FILTER, sec, body))


def course_section(items: list[dict]) -> str:
    """课程区块(标题行 + 按项目分组的课程树)。"""
    return _section("course", "课程", sum(1 for e in items if e["kind"] == "lesson"),
                    ICON_BOOK, course_tree(items), "只看未读的课")


def note_section(items: list[dict]) -> str:
    """笔记区块(标题行 + 视图切换 + 按项目视图的笔记树)。"""
    switch = ('<div class="view-switch" role="tablist" aria-label="笔记视图">'
              '<button class="view-btn" type="button" role="tab" data-view="project" aria-selected="true">按项目</button>'
              '<button class="view-btn" type="button" role="tab" data-view="tag" aria-selected="false">按标签</button>'
              '</div>')
    return _section("note", "笔记", sum(1 for e in items if e["kind"] == "note"),
                    ICON_NOTE, switch + note_tree(items), "只看未完成的笔记")
