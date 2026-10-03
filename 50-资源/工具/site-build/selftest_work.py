#!/usr/bin/env python3
"""工作台渲染自检:接线 / 骨架 / 两棵树 / 计数键 / 内联顺序 + 两条负向。

只读真实仓库与真实 `render_page` 产出,不写文件。单跑:
  cd 50-资源/工具/site-build && PYTHONIOENCODING=utf-8 python -B selftest_work.py
"""
from __future__ import annotations

import html as H
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

import build_site
import selftest_breakpoints
import selftest_cards
import selftest_notes
import selftest_side
import selftest_status_js
import selftest_tokens
import site_counts
import site_minify
import site_scan
import site_work_css
import site_work_js
import site_work_palette
import site_work_status
import site_work_status_css
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
ST_ITEM = re.compile(r'<button class="st-item[^"]*"[^>]*data-act="([^"]+)"')
STATUS_ACTS = ["welcome", "open", "read", "thecount", "theme", "split"]


def node_check(js: str) -> tuple[int, str]:
    """语法自检必须写临时文件:Windows 上 `node --check <(python …)` 读不了管道路径。"""
    node = shutil.which("node")
    assert node, "找不到 node,无法校验 JS 语法"
    with tempfile.TemporaryDirectory(prefix="status-check-") as tmp:
        p = Path(tmp) / "seg.js"
        p.write_text(js, encoding="utf-8")
        r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    return r.returncode, (r.stderr or "").strip()


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

    # 1b. 侧栏两区块(课程 / 笔记):无筛选 chip · 视图切换 · 分组默认展开 1 个 · 行高
    selftest_side.run(page, entries, items, ok)

    # 1c. 视觉标尺:间距只 5 档 / 字号只 6 档 / 语义色成对 / 图标 16px / 四态齐全(含负向)
    selftest_tokens.run(ok)

    # 1d. 项目卡重做 + 三处空状态(含一条负向)
    selftest_cards.run(page, entries, ok)

    # 1e. 五档断点 + 侧栏可拖拽 + 分屏前置(Task 8;第 4 条是 node 真跑的负向)
    selftest_breakpoints.run(ok)

    # 1f. 笔记正文惰性 <template>(静态)+ 实例化 / 坏 key 兜底(node 打桩)
    selftest_notes.run(page, entries, ok)

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
       site_minify.minify_js(site_work_palette.PALETTE_JS) in page and "style" not in site_work_palette.PALETTE_JS)

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

    # 6. 状态栏六段可点:六个 button.st-item 各有 data-act;六条分派都在;未知走默认
    acts = ST_ITEM.findall(page)
    ok("状态栏恰 6 个 button.st-item", len(acts) == 6, "实际 %d:%s" % (len(acts), acts))
    ok("状态栏 data-act 值集合 == 六段", sorted(acts) == sorted(STATUS_ACTS), str(acts))
    ok("旧 span 状态栏已换掉", 'class="statusbar"><span' not in page)
    js = site_work_status.STATUS_JS
    missing = [a for a in STATUS_ACTS if ('act === "%s"' % a) not in js]
    ok("六条动作各自有分派分支", not missing, "缺:%s" % missing)
    ok("STATUS_JS 按 button.st-item[data-act] 分派点击", "button.st-item[data-act]" in js)
    ok("STATUS_JS 无 eval / alert / 内联事件",
       "eval(" not in js and "alert(" not in js and "onclick" not in js)
    ok("STATUS_JS 计数详情读 window.__counts.get", "__counts" in js and ".get(" in js)
    ok("STATUS_JS 已内联进 WORK_JS", js in site_work_js.WORK_JS)
    rc, err = node_check(js)
    ok("STATUS_JS node --check 通过", rc == 0, err[-200:])
    # node 打桩实跑:六个动作各改变可观测状态;未知 data-act 走默认分支且不抛异常
    try:
        rows = selftest_status_js.run_probes()
        got = [r["act"] for r in rows]
        ok("打桩覆盖六个动作 + 未知", got == STATUS_ACTS + ["bogus"], str(got))
    except AssertionError as exc:
        rows = []
        ok("状态栏 node 打桩可跑", False, str(exc))
    for r in rows:
        ok("状态栏动作 %s 生效" % r["act"], r["pass"], r.get("error") or r.get("rec") or "")

    # 7. 状态栏 CSS:可点三态 + 桌面锁 24px + 窄窗口精简为 3 段(拼在 WORK_CSS 末尾)
    css = site_work_status_css.STATUS_CSS
    ok("状态栏 CSS 拼在 WORK_CSS 末尾", css == site_work_css.WORK_CSS[-len(css):])
    ok("状态栏 CSS:.st-item 悬停 / 焦点 / 按下 三态 + pointer",
       all(s in css for s in ("cursor:pointer", ".st-item:hover", ".st-item:active", ".st-item:focus-visible")))
    ok("状态栏 CSS:桌面锁 24px(靠 height:100% + line-height,不抬 min-height)",
       "height:100%" in css and "min-height" not in css)
    ok("窄窗口状态栏精简为 3 段(隐藏 thecount/theme/split)",
       "max-width:768px" in css and all(s in css for s in (".st-count", ".st-theme", ".st-split")))
    ok("计数浮层是自建 .st-pop(hidden 真隐藏,不用 alert)",
       ".st-pop[hidden]{display:none!important}" in css)

    print("结论:%s(%d 例,%d 失败)" % ("PASS" if FAIL == 0 else "FAIL", PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
