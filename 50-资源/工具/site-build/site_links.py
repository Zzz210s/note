#!/usr/bin/env python3
"""0-Note 在线阅读站 · 条目准备与站内链接改写。

从 `site_render.py` 拆出(守库规「每个 .py ≤ 200 行」)。两件事:
  1. `prepare()` 给扫描结果补渲染用的派生字段(锚点 / 类别 / 徽章 / 链接 / 显示名 / 摘要)
  2. `fix_md_links()` 把笔记正文里的站内链接改成站点可用的形式

链接规则(评审过的三条集成点,见 spec §5.3):
  - `class="wl"`(render_md 自己产的双链)不动
  - 同篇锚点 `#…` -> 本条目的锚点(笔记内部的标题锚点本站不生成 id,指向卡片比死链好)
  - `.md` 目标 -> 命中当前模式的条目就转锚点,否则退化成纯文字
  - `.html` 目标 -> 先按「链接所在目录 + 相对路径」归一,命中真实课文件就用它;
    再按课号兜底(笔记里的课链接常带过期前缀 `x1-`);都不中就退化成纯文字
"""
from __future__ import annotations

import posixpath
import re
import urllib.parse

from site_scan_lib import slugify

STATUS_OK = ("learning", "todo", "done", "not-started")
MD_HREF = re.compile(r'<a href="([^"]+)"([^>]*)>(.*?)</a>', re.S)


def entry_anchor(e: dict) -> str:
    """契约 5.3:每条的锚点 = `<项目slug>-<条目slug>`(全库唯一)。"""
    return "%s-%s" % (slugify(e["section"]) or "root", e["slug"])


def prepare(entries: list[dict]) -> list[dict]:
    out = []
    for raw in entries:
        e = dict(raw)
        p = e["path"]
        e["anchor"] = entry_anchor(e)
        e["status"] = e.get("status") if e.get("status") in STATUS_OK else ""
        e["kind_of"] = "course" if e["kind"] == "lesson" else ("know" if "/20-知识/" in p else "project")
        if e["kind"] == "lesson":
            e["type_badge"] = "course"
        elif e["kind"] == "index":
            e["type_badge"] = "index"
        elif p.startswith("90-模板/"):
            e["type_badge"] = "template"
        elif "/20-知识/" in p:
            e["type_badge"] = "know"
        elif e.get("type") == "log":
            e["type_badge"] = "log"
        else:
            e["type_badge"] = "project"
        code = re.search(r"/(?:x\d+-)?(\d{4})-", p)
        e["show_title"] = "%s · %s" % (code.group(1), e["title"]) if (e["kind"] == "lesson" and code) else e["title"]
        e["href"] = urllib.parse.quote(p) if e["kind"] == "lesson" else "#" + e["anchor"]
        e["sum"] = summary_of(e)
        e["text"] = plain_text(e.get("body") or "")
        out.append(e)
    return out


def summary_of(e: dict) -> str:
    """摘要兜底:像命令 / 太短 / 空 -> 退回标题。"""
    s = (e.get("summary") or "").strip()
    if len(s) < 6 or s.startswith(("$", "#", "```", "|")) or "<< EOF" in s:
        return e["title"]
    return s


def plain_text(body: str) -> str:
    s = re.sub(r"```.*?```", " ", body, flags=re.S)
    s = re.sub(r"[#>*`|\[\]()-]+", " ", s)
    return " ".join(s.split())


def known_map(items: list[dict]) -> dict:
    """「条目名 / 文件名主干 / slug / 标题 -> 最终锚点」。双链与 `.md` 链接都查它。"""
    m: dict[str, str] = {}
    for e in items:
        stem = re.sub(r"\.(?:md|html)$", "", e["path"].rsplit("/", 1)[-1])
        for key in (stem, slugify(stem), e["slug"], e["title"], slugify(e["title"])):
            m.setdefault(key, e["anchor"])
    return m


def lesson_ctx() -> tuple[set[str], dict[str, str]]:
    """全库课程的真实路径集合与「课号 -> 路径」映射(修正笔记里的相对 .html 链接)。"""
    import site_scan
    paths: set[str] = set()
    by_code: dict[str, str] = {}
    for e in site_scan.scan("all"):
        if e["kind"] == "lesson":
            paths.add(e["path"])
            m = re.search(r"/(?:x\d+-)?(\d{4})-", e["path"])
            if m:
                by_code.setdefault(m.group(1), e["path"])
    return paths, by_code


def _norm(base_dir: str, rel: str) -> str:
    rel = urllib.parse.unquote(rel)
    return posixpath.normpath(rel[1:] if rel.startswith("/") else posixpath.join(base_dir, rel))


def fix_md_links(frag: str, known: dict, *, base_dir: str = "", anchor: str = "",
                 lesson_paths: set[str] | None = None, lesson_by_code: dict[str, str] | None = None) -> str:
    lesson_paths = lesson_paths or set()
    lesson_by_code = lesson_by_code or {}

    def sub(m: re.Match) -> str:
        href, attrs, text = m.group(1), m.group(2), m.group(3)
        if 'class="wl"' in attrs:
            return m.group(0)
        if href.startswith("#"):
            return '<a href="#%s">%s</a>' % (anchor, text) if anchor else text
        path = href.split("#")[0]
        low = path.lower()
        if low.endswith(".md"):
            stem = re.sub(r"\.md$", "", posixpath.basename(path), flags=re.I)
            a = known.get(stem) or known.get(slugify(stem))
            return '<a class="wl" href="#%s">%s</a>' % (a, text) if a else text
        if low.endswith(".html"):
            norm = _norm(base_dir, path)
            if norm in lesson_paths:
                return '<a href="%s">%s</a>' % (urllib.parse.quote(norm), text)
            m2 = re.search(r"(?:^|/)(?:x\d+-)?(\d{4})-", path)
            if m2 and m2.group(1) in lesson_by_code:
                return '<a href="%s">%s</a>' % (urllib.parse.quote(lesson_by_code[m2.group(1)]), text)
            return text
        return m.group(0)

    return MD_HREF.sub(sub, frag)
