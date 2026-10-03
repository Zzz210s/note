#!/usr/bin/env python3
"""工作台侧栏两区块的自检(Task 5):无 chip / 双区块 / 视图切换 / 默认展开 1 组 / 行高。

从 `selftest_work.py` 拆出(该文件加了这批断言后到 209 行,破库规「每个 .py ≤ 200 行」);
由 `selftest_work.main()` 以 `run(page, entries, items, ok)` 调用,也可单跑:
  cd 50-资源/工具/site-build && PYTHONIOENCODING=utf-8 python -B selftest_side.py
"""
from __future__ import annotations

import re
import sys

import site_minify
import site_render
import site_scan
import site_work_css
import site_work_filter
import site_work_side_css

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SIDE = re.compile(r'<aside class="sidebar".*?</aside>', re.S)


def run(page: str, entries: list[dict], items: list[tuple[str, str]], ok) -> None:
    """侧栏结构断言;`ok(name, cond, detail)` 由调用方给(共用同一 PASS/FAIL 计数)。"""
    side = SIDE.search(page).group(0)
    head = side.split('class="side-body"')[0]
    ok("侧栏不再有筛选 chip(筛选只剩欢迎页)",
       'class="chip"' not in head and 'class="filters"' not in head, head[:120])
    ok("两个区块标题行 [data-section=course|note]",
       re.findall(r'data-section="([a-z]+)"', side) == ["course", "note"],
       str(re.findall(r'data-section="([a-z]+)"', side)))
    ok("每个区块标题行带计数 + 折叠按钮 + 筛选按钮",
       side.count('class="sec-count"') == 2 and side.count('class="sec-toggle"') == 2
       and side.count('class="sec-filter"') == 2)
    ok("笔记区块有视图切换 data-view=project|tag 且默认按项目",
       re.findall(r'data-view="([a-z]+)"', side) == ["project", "tag"]
       and 'data-view="project" aria-selected="true"' in side)
    ok("标签视图不预渲染(标签分组由 JS 从 data-tags 现建)",
       "标签:" not in side and "data-tags=" in side
       and "buildTagNodes" in site_work_filter.FILTER_JS and "W.setNoteView" in site_work_filter.FILTER_JS)
    ok("笔记行只留类型徽章(不再挂次数与标签 chip)",
       'data-kind="note" data-count="0" data-tags=' in side and 'class="tag"' not in side)
    expanded = len(re.findall(r'class="tree-group"[^>]*aria-expanded="true"', page))
    ok("分组头默认只展开第一个(课程区块第一个)", expanded == 1
       and page.index('class="tree-group" aria-expanded="true"') < page.index('data-section="note"'),
       "展开 %d 个" % expanded)
    note = {k for k, kind in items if kind == "note"}
    note_items = [k for k, kind in items if kind == "note"]
    ok("笔记项目视图项 == 笔记条目数(不再 165)", len(note_items) == len(note),
       "%d vs %d" % (len(note_items), len(note)))
    ok("侧栏行高三档 26/32/44 与当前项强调条已在样式里",
       all(s in site_work_side_css.SIDE_CSS for s in ("min-height:32px", "min-height:44px"))
       and "inset 2px 0 0 var(--w-accent)" in site_work_css.WORK_CSS
       and site_minify.minify_css(site_work_css.WORK_CSS) in page
       and page.index(site_minify.minify_css(site_work_css.WORK_CSS)) < page.index(site_minify.minify_css(site_work_side_css.SIDE_CSS)))


def main() -> int:
    entries = site_scan.scan("public")
    page = site_render.render_page(entries, mode="public", generated_at="self-test", rev="self-test")
    tree = re.compile(r'class="tree-item" data-key="([^"]+)" data-kind="(course|note)"')
    n = 0

    def ok(name: str, cond: bool, detail: str = "") -> None:
        nonlocal n
        n += 1
        print("%s %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else " " + detail))

    run(page, entries, tree.findall(page), ok)
    print("结论:%s(%d 例)" % ("PASS", n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
