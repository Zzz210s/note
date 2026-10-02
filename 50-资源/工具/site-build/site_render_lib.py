#!/usr/bin/env python3
"""site_render 的条目卡构造与链接工具(拆模块以守库规 200 行上限)。

DOM/属性契约的唯一真源是 `site_dom.CONTRACT`;本模块只产 HTML 片段与上下文,
不拼整页(整页在 `site_render`,项目卡/排序/索引在 `site_render_data`)。

三条集成事项在此落地:① 正文里相对 `.md` 内链转站内锚点,解不到就退化成
纯文字;② 双链锚点用 `known`(目标 -> 最终锚点)对齐 `#<项目slug>-<条目slug>`;
③ `known` 只含本次 entries,所以对外页不会出现指向非公开条目的死锚点。
"""
from __future__ import annotations

import html
import posixpath
import re
import urllib.parse
from pathlib import Path

from site_md import render_md
from site_scan_lib import html_text, slugify

ANCHOR = re.compile(r'<a href="([^"]+)">(.*?)</a>', re.S)
SCHEME = re.compile(r"^[a-zA-Z][\w+.\-]*:")
EXT = re.compile(r"\.(?:md|html)$")
STATES = ("learning", "todo", "done", "not-started")
STATE_CN = {"learning": "学习中", "todo": "待办", "done": "已完成", "not-started": "未开始"}
KIND_CN = {"course": "课程", "know": "知识", "project": "项目"}
TYPE_CN = {"course": "课程", "know": "知识", "project": "项目", "log": "记录",
           "index": "索引", "template": "模板"}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def norm_status(s: str) -> str:
    return s if s in STATES else ""


def project_slug(section: str) -> str:
    return slugify(section)


def entry_anchor(entry: dict) -> str:
    return "%s-%s" % (project_slug(entry["section"]), entry["slug"])


def entry_href(entry: dict) -> str:
    if entry["kind"] == "lesson" or entry["path"].endswith(".html"):
        return urllib.parse.quote(entry["path"])
    return "#" + entry_anchor(entry)


def display_title(entry: dict) -> str:
    if entry["kind"] != "lesson":
        return entry["title"]
    m = re.search(r"(\d{4})", Path(entry["path"]).stem)
    return "%s · %s" % (m.group(1), entry["title"]) if m else entry["title"]


def card_kind(entry: dict) -> str:
    if entry["kind"] == "lesson":
        return "course"
    return "know" if "/20-知识/" in entry["path"] else "project"


def badge_type(entry: dict) -> str:
    if entry["kind"] == "lesson":
        return "course"
    if "/20-知识/" in entry["path"]:
        return "know"
    if entry["kind"] == "index":
        return "index"
    if entry["kind"] == "scaffold":
        return "template"
    return "log" if "/记录/" in entry["path"] else "project"


def summary_text(entry: dict) -> str:
    """摘要兜底:看起来是命令(`$` / `>` / `#` 开头或含 heredoc)就退回标题。"""
    s = entry["summary"] or entry["title"]
    if s.startswith(("$", ">", "#")) or "<< EOF" in s:
        return entry["title"]
    return s


def known_map(entries: list[dict]) -> dict[str, str]:
    """「目标名 -> 最终卡片锚点」;供 render_md 解析 `[[双链]]`(值不含 `#`)。"""
    known: dict[str, str] = {}
    for e in entries:
        a = entry_anchor(e)
        stem = EXT.sub("", e["path"].rsplit("/", 1)[-1])
        keys = [stem, slugify(stem), e["slug"], e["title"], slugify(e["title"]),
                EXT.sub("", e["path"])]
        if e["path"].startswith("10-项目/"):
            keys.append(EXT.sub("", e["path"][len("10-项目/"):]))
        for k in keys:
            known.setdefault(k, a)
    return known


def build_ctx(entries: list[dict]) -> dict:
    return {"entries": entries, "known": known_map(entries),
            "by_path": {e["path"]: e for e in entries}, "cache": {},
            "ids": {"main"} | {entry_anchor(e) for e in entries}}


def render_body(entry: dict, ctx: dict) -> tuple[str, str]:
    """(正文 HTML, 纯文本);同一篇只渲染一次,卡片与搜索索引共用。"""
    if entry["path"] not in ctx["cache"]:
        raw = rewrite_links(render_md(entry["body"], known=ctx["known"]), entry, ctx)
        ctx["cache"][entry["path"]] = (raw, html_text(raw))
    return ctx["cache"][entry["path"]]


def rewrite_links(frag: str, entry: dict, ctx: dict) -> str:
    """相对内链:站内有目标 -> 锚点(笔记)/ 课文件 URL(.html);没有 -> 纯文字。

    纯 `#锚点` 链接只在页内确实存在该 id 时保留,否则退化(防死锚点)。
    """
    base = posixpath.dirname(entry["path"])

    def sub(m: re.Match) -> str:
        href, text = m.group(1), m.group(2)
        if href.startswith("#"):
            return m.group(0) if href[1:] in ctx["ids"] else text
        if SCHEME.match(href) or href.startswith("//"):
            return m.group(0)
        path, _, frag2 = href.partition("#")
        target = ctx["by_path"].get(
            posixpath.normpath(posixpath.join(base, urllib.parse.unquote(path))))
        if not target:
            return text
        if target["path"].endswith(".html"):
            return '<a href="%s%s">%s</a>' % (urllib.parse.quote(target["path"]),
                                              "#" + frag2 if frag2 else "", text)
        return '<a href="#%s">%s</a>' % (entry_anchor(target), text)

    return ANCHOR.sub(sub, frag)


def _rel(entry: dict, ctx: dict) -> str:
    items = []
    for name in entry.get("related") or []:
        a = ctx["known"].get(name) or ctx["known"].get(slugify(name))
        items.append('<a href="#%s">%s</a>' % (a, esc(name)) if a
                     else "<span>%s</span>" % esc(name))
    return '<div class="card-rel"><span>相关:</span>%s</div>' % "".join(items) if items else ""


def card(entry: dict, ctx: dict) -> str:
    st = norm_status(entry["status"])
    bt = badge_type(entry)
    out = ['<article class="card" id="%s" data-kind="%s" data-status="%s">'
           % (esc(entry_anchor(entry)), card_kind(entry), st),
           '<div class="card-head"><h3 class="card-title"><a href="%s">%s</a></h3>'
           % (esc(entry_href(entry)), esc(display_title(entry))),
           '<div class="card-meta"><span class="badge" data-type="%s">%s</span>'
           % (bt, esc(entry["type"] or TYPE_CN[bt]))]
    if st:
        out.append('<span class="badge" data-status="%s">%s</span>' % (st, STATE_CN[st]))
    if entry["date"]:
        out.append('<span class="when">%s</span>' % esc(entry["date"]))
    out.append('</div></div><p class="card-sum">%s</p>' % esc(summary_text(entry)))
    if entry["kind"] == "note" and entry["body"]:
        out.append('<div class="card-body">%s</div>' % render_body(entry, ctx)[0])
    if entry["win"]:
        out.append('<p class="card-win">%s</p>' % esc(entry["win"]))
    out.append(_rel(entry, ctx))
    out.append("</article>")
    return "".join(out)
