#!/usr/bin/env python3
"""工作台渲染自检:接线 / 骨架 / 两棵树 / 计数键 / 内联顺序 + 两条负向。

只读真实仓库与真实 `render_page` 产出,不写文件。单跑:
  cd 50-资源/工具/site-build && PYTHONIOENCODING=utf-8 python -B selftest_work.py
"""
from __future__ import annotations

import html as H
import json
import re
import sys
import urllib.parse
from pathlib import Path

import build_site
import site_counts
import site_scan
import site_work_js
import site_work_palette
import site_render

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT_ROOT = Path(__file__).resolve().parents[3]
PASS = FAIL = 0

COUNTS_SEG = re.compile(r'window\.__COUNTS__=(.*?);</script>', re.S)
TREE_ITEM = re.compile(r'class="tree-item" data-key="([^"]+)" data-kind="(course|note)"')
COURSE_HREF = re.compile(r'<button class="tree-item" data-key="([^"]+)" data-kind="course" '
                         r'data-count="\d+" data-href="([^"]+)"')
DATA_SRC = re.compile(r'(data-src=")[^"]*(")')


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS", name)
    else:
        FAIL += 1
        print("FAIL", name, detail)


def counts_keys(page: str) -> list[str]:
    m = COUNTS_SEG.search(page)
    assert m, "页面缺 window.__COUNTS__ 段"
    return list(json.loads(m.group(1)).keys())


def slug_errors(keys) -> list[str]:
    """计数键必须是 slug:非空、不含 `/`、不以 .md/.html 结尾(路径键会让前端全部落空)。"""
    return [k for k in keys if not k or "/" in k or k.endswith((".md", ".html"))]


def main() -> int:
    entries = site_scan.scan("public")
    live = build_site.live_counts()
    page = site_render.render_page(entries, mode="public", generated_at="self-test", rev="self-test")

    # 1. 欢迎页只包一层;两棵树与实时计数一致;课树项都有 data-href 且文件存在
    n_welcome = page.count('class="group-body" data-kind="welcome"')
    ok("欢迎页容器只包一层(2 组各一)", n_welcome == 2, "实际 %d" % n_welcome)
    ok("group-body 恰 6 个(2 组 x 3 面板)", page.count('class="group-body"') == 6,
       "实际 %d" % page.count('class="group-body"'))
    items = TREE_ITEM.findall(page)
    course = [k for k, kind in items if kind == "course"]
    note = {k for k, kind in items if kind == "note"}
    ok("课程树项数 == 实时 lessons", len(course) == live["lessons"],
       "%d vs %d" % (len(course), live["lessons"]))
    ok("笔记树去重 key == 实时 20-知识+记录", len(note) == live["know"] + live["records"],
       "%d vs %d" % (len(note), live["know"] + live["records"]))
    ok("两棵树去重 key 合计 == 对外条目数", len(set(course) | note) == len(entries),
       "%d vs %d" % (len(set(course) | note), len(entries)))
    hrefs = COURSE_HREF.findall(page)
    ok("每个课树项都有 data-href", len(hrefs) == len(course), "%d vs %d" % (len(hrefs), len(course)))
    missing = [h for _k, h in hrefs
               if not (VAULT_ROOT / urllib.parse.unquote(H.unescape(h))).exists()]
    ok("每个课树项 data-href 都指向真实文件", not missing, str(missing[:3]))

    # 2. window.__COUNTS__ 的键集合 == bake(entries),且都是 slug(不是路径)
    keys = counts_keys(page)
    baked = set(site_counts.bake(entries).keys())
    ok("__COUNTS__ 键集合 == site_counts.bake(entries)", set(keys) == baked,
       "%s vs %s" % (sorted(keys)[:3], sorted(baked)[:3]))
    ok("__COUNTS__ 键都是 slug(非路径)", not slug_errors(keys), str(slug_errors(keys)[:3]))

    # 3. 三段 JS 都不含旧 beacon;WORK_BOOT 在 <style> 之前;palette 只留行为
    for seg, name in ((site_counts.COUNTS_JS, "COUNTS_JS"), (site_work_js.WORK_JS, "WORK_JS"),
                      (site_work_palette.PALETTE_JS, "PALETTE_JS")):
        ok("%s 不含 lesson-close-beacon" % name, "lesson-close-beacon" not in seg)
    ok("WORK_BOOT 出现在 <style> 之前",
       page.index(site_work_js.WORK_BOOT) < page.index("<style>"))
    ok("PALETTE_JS 已内联且不再自注入 <style>",
       site_work_palette.PALETTE_JS in page and "style" not in site_work_palette.PALETTE_JS)

    # 4. 负向:种子原文(路径键)必须被 slug 检查拦下
    path_keys = list(json.loads(site_counts.seed_json(None)).keys())
    ok("负向:不传 entries 得到路径键,slug 检查会拦",
       bool(slug_errors(path_keys)) and "/" in path_keys[0], str(path_keys[:1]))

    # 5. 负向:课 iframe 的 data-src 指向不存在文件 -> build_site.check() 报错
    bad_page = DATA_SRC.sub(lambda m: m.group(1) + "no/such/lesson.html" + m.group(2), page, count=1)
    errs = build_site.check("public", entries, bad_page)
    ok("负向:data-src 指向不存在文件被 check 拦", any("data-src" in e for e in errs), str(errs))
    ok("正向:真页面 check 无错", build_site.check("public", entries, page) == [],
       str(build_site.check("public", entries, page))[:200])

    print("结论:%s(%d 例,%d 失败)" % ("PASS" if FAIL == 0 else "FAIL", PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
