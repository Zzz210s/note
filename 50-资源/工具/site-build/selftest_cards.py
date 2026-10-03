#!/usr/bin/env python3
"""项目卡重做 + 三处空状态自检(由 `selftest_work` 调用,读真实页面与真实 CSS 源码)。

四条口径(设计 §7):每张卡有色块 / 标题 / 定位 / 三统计 / 进度条;网格 auto-fill +
`minmax(260px,1fr)` + `max-width` 封顶 4 列;欢迎页 / 搜索面板 / 侧栏筛选三处空状态各带
一个动作按钮;负向 —— 项目定位为空时卡片仍渲染且不出现 `undefined`。
单跑:`PYTHONIOENCODING=utf-8 python -B selftest_cards.py`
"""
from __future__ import annotations

import re
import sys

import site_parts
import site_work_css
import site_work_panels

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GRID_RULE = re.compile(r"\.proj-grid\{([^}]*)\}")
MARK_COLOR = re.compile(r'class="proj-mark" data-color="([^"]+)"')
CARD_ATTR = 'class="proj-card" data-color="'
PASS = FAIL = 0


def _cards(page: str) -> list[str]:
    """欢迎页项目卡网格里的每张卡(截到首个 section.sec 为止,避开正文卡片)。"""
    start = page.index('<div class="proj-grid"')
    end = page.index('<section class="sec"', start)
    return page[start:end].split('<div ' + CARD_ATTR)[1:]


def run(page: str, entries: list[dict], ok) -> None:
    cards = _cards(page)
    n_sections = len({e["section"] for e in entries})
    ok("项目卡数 == 项目数", len(cards) == n_sections, "%d vs %d" % (len(cards), n_sections))

    bad = [i for i, c in enumerate(cards) if not (
        'class="proj-mark" data-color="' in c and 'class="proj-head"' in c
        and 'class="proj-name"' in c and 'class="proj-desc"' in c
        and 'class="proj-stats"' in c and c.count("<b>") == 3
        and 'class="proj-prog"' in c and 'value="' in c and 'max="' in c)]
    ok("每张卡含 色块/标题/定位/三统计/进度条", bool(cards) and not bad, "缺项卡:%s" % bad[:3])

    colors = {m.group(1) for m in MARK_COLOR.finditer(page)}
    ok("色块颜色随项目不同(≥2 种语义色)", len(colors) >= 2, sorted(colors))

    rule = GRID_RULE.search(site_work_css.WORK_CSS)
    css = rule.group(1) if rule else ""
    ok("网格 auto-fill + minmax(260px,1fr) + max-width 封顶 4 列",
       "auto-fill" in css and "minmax(260px,1fr)" in css and "max-width" in css
       and "--proj-max:calc(260px*4 + var(--s3)*3)" in site_work_css.WORK_CSS, css)

    search = site_work_panels.SEARCH_PANEL_HTML
    ok("三处空状态各带动作按钮(欢迎页 / 搜索 / 侧栏)",
       'id="empty"' in page and 'id="clear2"' in page
       and 'panel-empty' in search and 'pe-btn' in search
       and 'id="side-empty"' in page and 'id="side-clear"' in page)

    fake = [{"kind": "lesson", "kind_of": "course", "status": "done", "slug": "x"}]
    html = site_parts.project_grid([("无定位的虚构项目", "fake", fake)])
    ok("负向:定位为空仍渲染且无 undefined",
       'class="proj-card"' in html and "undefined" not in html
       and "暂无定位说明" in html, html[:120])


def main() -> int:
    global PASS, FAIL
    PASS = FAIL = 0

    def _ok(name, cond, detail=""):
        global PASS, FAIL
        if cond:
            PASS += 1
            print("PASS", name)
        else:
            FAIL += 1
            print("FAIL", name, detail)

    import site_render
    import site_scan
    entries = site_scan.scan("public")
    page = site_render.render_page(entries, mode="public", generated_at="self-test", rev="self-test")
    run(page, entries, _ok)
    print("结论:%s(%d 例,%d 失败)" % ("PASS" if not FAIL else "FAIL", PASS + FAIL, FAIL))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
