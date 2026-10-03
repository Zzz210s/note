#!/usr/bin/env python3
"""0-Note 在线阅读站 · 页面零件(图标 / 总览 / 筛选 / 项目卡 + 工作台两棵树 / 状态栏)。

这些零件只产出 HTML 片段,不含任何业务判断:谁进页面、进哪一节由 `site_render`
决定;DOM 形状照 `site_dom.CONTRACT`(唯一真源)。本模块不读磁盘,只吃条目 dict。
"""
from __future__ import annotations

import html as H
import re
import sys
from pathlib import Path

from site_scan_lib import html_text
from site_counts import bake

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT_ROOT = Path(__file__).resolve().parents[3]

# 徽章 data-type 取值(契约枚举):course / know / project / log / index / template
KIND_LABEL = {"course": "课程", "know": "知识", "project": "项目"}
STATUS_LABEL = {"learning": "学习中", "todo": "待做", "done": "已完成", "not-started": "未开始"}

ICON = {
    "search": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/>'
              '<path d="M16.5 16.5 21 21"/></svg>',
    "close": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6 18 18M18 6 6 18"/></svg>',
    "theme": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v3M12 18v3M3 12h3M18 12h3'
             'M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/><circle cx="12" cy="12" r="4"/></svg>',
    "menu": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    "up": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20V5M6 11l6-6 6 6"/></svg>',
    "files": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h11l5 5v11H4z"/>'
             '<path d="M15 4v5h5"/></svg>',
    "terminal": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7l5 5-5 5M13 17h6"/></svg>',
}


def intro(section: str) -> str:
    """项目一句话定位:优先 MISSION.md,其次 !项目说明.md 的第一个散文段;都没有就空串。"""
    for name in ("MISSION.md", "!项目说明.md"):
        p = VAULT_ROOT / section / name
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith(("---", "#", ">", "-", "|", "!", "`")) or ":" in s[:14]:
                continue
            s = html_text(s)
            if len(s) >= 8:
                return s[:80]
    return ""


def overview(entries: list[dict], *, generated_at: str, rev: str, title: str) -> str:
    courses = sum(1 for e in entries if e["kind"] == "lesson")
    sections = len({e["section"] for e in entries})
    latest = sorted([e for e in entries if e.get("date")], key=lambda e: e["date"], reverse=True)[:5]
    latest_html = " · ".join('<a href="#%s">%s</a>' % (e["anchor"], H.escape(e["title"][:18])) for e in latest)
    return (
        '<div class="overview"><span><b>%s</b> 共 <b>%d</b> 条 · 项目 <b>%d</b> 个 · 课程 <b>%d</b> 节'
        ' · 生成 %s · 来源 %s<br>最近更新:%s</span></div>'
        % (H.escape(title), len(entries), sections, courses, H.escape(generated_at), H.escape(rev), latest_html)
    )


def chips(entries: list[dict]) -> str:
    kinds = [k for k in ("course", "know", "project") if any(e["kind_of"] == k for e in entries)]
    states = [s for s in STATUS_LABEL if any(e["status"] == s for e in entries)]
    if len(kinds) < 2:
        kinds = []
    out = ['<div class="filters"><span class="lbl">筛选:</span>']
    for k in kinds:
        out.append('<button class="chip" data-group="kind" data-value="%s" aria-pressed="false">%s<span class="n"></span></button>'
                   % (k, KIND_LABEL[k]))
    if kinds and states:
        out.append('<span class="lbl">·</span>')
    for s in states:
        out.append('<button class="chip" data-group="status" data-value="%s" aria-pressed="false">%s<span class="n"></span></button>'
                   % (s, STATUS_LABEL[s]))
    out.append('</div>')
    return "".join(out)


def project_grid(sections: list[tuple[str, str, list[dict]]]) -> str:
    cards = []
    for name, _slug, items_ in sections:
        done = sum(1 for e in items_ if e["status"] == "done")
        courses = sum(1 for e in items_ if e["kind"] == "lesson")
        know = sum(1 for e in items_ if e["kind_of"] == "know")
        desc = intro(name)
        cards.append(
            '<div class="proj-card"><h3 class="proj-name">%s</h3><p class="proj-desc">%s</p>'
            '<div class="proj-stats"><span>知识 <b>%d</b></span><span>课程 <b>%d</b></span>'
            '<span>已完成 <b>%d</b>/%d</span></div>'
            '<progress class="proj-prog" value="%d" max="%d" aria-label="%s 完成度"></progress></div>'
            % (H.escape(name), H.escape(desc or "—"), know, courses, done, len(items_),
               done, len(items_), H.escape(name))
        )
    return '<div class="proj-grid">%s</div>' % "".join(cards)


def slug_of(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff-]", "-", name)


# ===== 工作台:状态栏(契约见 site_dom.CONTRACT「工作台页」;两棵树已拆到 site_side) =====
def statusbar(items: list[dict], *, theme: str = "浅色", split: str = "单栏") -> str:
    """状态栏六段:全部可点(契约 `site_dom.CONTRACT`「工作台页」)。

    段 -> `data-act`:条目数 = welcome(回空态)/ 打开数 = open(命令面板)/ 课程进度 =
    read(只筛未读课)/ 本课次数 = thecount(计数详情浮层)/ 主题 = theme / 分栏 = split。
    数字是首屏初值,JS(`site_work_status`)会按需回填(打开数 / 本课次数 / 已读进度)。
    """
    baked = bake(items)
    lessons = [e for e in items if e["kind"] == "lesson"]
    read = sum(1 for e in lessons if (baked.get(e["slug"]) or {}).get("count", 0) > 0)

    def btn(cls: str, act: str, text: str, title: str) -> str:
        return ('<button class="st-item %s" data-act="%s" type="button" title="%s">%s</button>'
                % (cls, act, title, text))

    return ('<footer class="statusbar">'
            + btn("st-items", "welcome", "%d 条" % len(items), "打开欢迎页(清空当前组标签)")
            + btn("st-open", "open", "打开 0", "打开命令面板")
            + btn("st-progress", "read", "课程已读 %d/%d" % (read, len(lessons)), "只看未读的课")
            + btn("st-count", "thecount", "本课 0 次", "当前课的计数详情")
            + btn("st-theme", "theme", theme, "切换主题")
            + btn("st-split", "split", split, "切换分栏(Ctrl+\\)")
            + '</footer>')
