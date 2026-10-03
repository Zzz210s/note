#!/usr/bin/env python3
"""工作台面板自检:三个面板容器 / 搜索控件 / 命令面板 17 条 / 键盘 / node 打桩逐条实跑。

只读真实仓库与真实 `render_page` 产出,不写仓库文件(临时 JS 写在系统临时目录)。
跑法:`cd 50-资源/工具/site-build && PYTHONIOENCODING=utf-8 python -B selftest_panels.py`

口径(契约 `site_dom.CONTRACT`「工作台页」一段 + Task 2 / Task 3 简报):
  · `aside.sidebar` 下恰有三个 `.side-body[data-panel=files|search|commands]`,内容各不相同;
  · 搜索面板含 `#panel-q` / `#panel-scope` / `#panel-results` / `#panel-empty`;
  · 命令面板含 `#cmds-list`,恰 17 条(全部启用;`note-view` 于 Task 5 侧栏重做后启用);
    RUN 键集合 == 启用集合;
  · `CMDS_JS` 带 ↑↓ / Enter / Esc 与 aria-current;`FILTER_JS` 发布 `W.onlyUnread` 且 `#clear2` 复位;
  · node 打桩载入真 `CMDS_JS` 逐条点击 16 条启用命令,断言每条改变可观测状态;
  · `PANELS_JS` 无旧 beacon、无 `eval`、无 `innerHTML`,`node --check` 通过(临时文件,不用进程替换)。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import selftest_panels_js
import site_render
import site_scan
import site_work_cmds as CM
import site_work_filter
import site_work_panels as P

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = FAIL = 0
PANEL_OPEN = re.compile(r'<div class="side-body[^"]*" data-panel="([a-z]+)"')
ORDER = ["files", "search", "commands"]


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS", name)
    else:
        FAIL += 1
        print("FAIL", name, detail)


def sidebar_of(page: str) -> str:
    m = re.search(r'<aside class="sidebar".*?</aside>', page, re.S)
    assert m, "页面缺 aside.sidebar"
    return m.group(0)


def body_map(side: str) -> dict[str, str]:
    """按 `.side-body[data-panel]` 起始位置切块;最后一块到 `</aside>` 为止。"""
    hits = list(PANEL_OPEN.finditer(side))
    stop = side.rfind("</aside>")
    out = {}
    for i, h in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else stop
        out[h.group(1)] = side[h.start():end]
    return out


def _text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def panel_problems(side: str) -> list[str]:
    """返回面板问题清单;空表示「三个面板都在且内容各不相同」。"""
    vals = [h.group(1) for h in PANEL_OPEN.finditer(side)]
    bodies = body_map(side)
    sigs = [_text(b) for b in bodies.values()]
    if vals != ORDER or len(bodies) != 3 or len(set(sigs)) != 3:
        return ["三个面板内容相同或 data-panel 取值异常:%s" % vals]
    return []


def node_check(js: str) -> tuple[int, str]:
    node = shutil.which("node")
    assert node, "找不到 node,无法校验 PANELS_JS 语法"
    with tempfile.TemporaryDirectory(prefix="panels-js-") as tmp:
        p = Path(tmp) / "panels.js"
        p.write_text(js, encoding="utf-8")
        r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    return r.returncode, (r.stderr or "").strip()


def main() -> int:
    entries = site_scan.scan("public")
    page = site_render.render_page(entries, mode="public", generated_at="self-test", rev="self-test")
    side = sidebar_of(page)

    # 1. 三个面板容器都在且内容各不相同
    ok("三个面板都在且内容各不相同", panel_problems(side) == [], str(panel_problems(side)))

    # 2. 搜索面板控件齐全
    search = body_map(side).get("search", "")
    for vid in ("panel-q", "panel-scope", "panel-results", "panel-empty"):
        ok("搜索面板含 #%s" % vid, ('id="%s"' % vid) in search)
    ok("范围下拉含 全部/课程/笔记/标签", all((">%s<" % s) in search for s in ("全部", "课程", "笔记", "标签")))
    ok("空状态含三个示例词", all((">%s<" % w) in search for w in ("伪终端", "恢复密钥", "tmux")))

    # 3. 命令面板:17 条(16 启用 + 1 禁用占位),HTML id 与 CMDS 表逐一对齐
    cmds = body_map(side).get("commands", "")
    ok("命令面板含 #cmds-list", 'id="cmds-list"' in cmds)
    html_ids = re.findall(r'data-cmd="([a-z-]+)"', cmds)
    ok("命令 id 集合 == site_work_cmds.CMDS", html_ids == [c[0] for c in CM.CMDS],
       "%s vs %s" % (html_ids, [c[0] for c in CM.CMDS]))
    ok("命令 17 条全部启用",
       len(html_ids) == 17 and len(CM.ENABLED) == 17 and CM.DISABLED == [],
       "%d 条 / 启用 %d" % (len(html_ids), len(CM.ENABLED)))
    ok("note-view 已启用(不再是禁用占位)",
       "note-view" in CM.ENABLED and 'data-cmd="note-view"' in cmds and " disabled" not in cmds)
    ok("渲染出的 disabled 为 0", cmds.count(" disabled ") == 0,
       "实际 %d" % cmds.count(" disabled "))
    # RUN 键集合 == 启用集合:既拦住「点了没反应」的空命令,也拦住孤儿处理函数
    m = re.search(r"var RUN = \{(.*?)\n  \};", CM.CMDS_JS, re.S)
    keys = re.findall(r'"([a-z-]+)":', m.group(1)) if m else []
    ok("CMDS_JS.RUN 键集合 == 启用命令集合", sorted(keys) == sorted(CM.ENABLED),
       "%s vs %s" % (sorted(keys), sorted(CM.ENABLED)))
    ok("命令面板键盘 ↑↓ / Enter / Esc / aria-current",
       all(k in CM.CMDS_JS for k in ("ArrowDown", "ArrowUp", 'k === "Enter"', 'k === "Escape"', "aria-current")))
    ok("CMDS_JS 无 eval / innerHTML", "eval(" not in CM.CMDS_JS and "innerHTML" not in CM.CMDS_JS)

    # 3b. 只看未完成 / 清空筛选:过滤接口发布 + #clear2 复位
    ok("FILTER_JS 发布 W.onlyUnread", "W.onlyUnread" in site_work_filter.FILTER_JS)
    ok("FILTER_JS 的 #clear2 复位 only-unread",
       re.search(r't\.closest\("#clear2"\)[\s\S]{0,120}?unread = false;', site_work_filter.FILTER_JS) is not None)
    ok("PANELS_JS 发布 W.searchScope", "W.searchScope" in P.PANELS_JS)

    # 4. PANELS_JS 洁净 + 语法
    ok("PANELS_JS 不含 lesson-close-beacon", "lesson-close-beacon" not in P.PANELS_JS)
    ok("PANELS_JS 不含 eval(", "eval(" not in P.PANELS_JS)
    ok("PANELS_JS 不用 innerHTML(命中片段走 DOM)", "innerHTML" not in P.PANELS_JS)
    rc, err = node_check(P.PANELS_JS)
    ok("PANELS_JS node --check 通过", rc == 0, err[-200:])

    # 5. 负向:三个面板容器改成同一 data-panel / 同内容,必须被拦
    dup = re.sub(r'(data-panel=")(?:search|commands)"', r'\g<1>files"', side)
    ok("负向:data-panel 全同值被拦", any("相同" in p for p in panel_problems(dup)),
       str(panel_problems(dup)))
    fake = ('<aside class="sidebar">'
            + "".join('<div class="side-body" data-panel="%s"><p>同样的内容</p></div>' % p for p in ORDER)
            + "</aside>")
    ok("负向:三相面板内容相同被拦", any("相同" in p for p in panel_problems(fake)),
       str(panel_problems(fake)))

    # 6. node 打桩:载入真 CMDS_JS,逐条点击 16 条启用命令,断言状态变化
    try:
        rows = selftest_panels_js.run_cmd_probes()
        ok("打桩命令集合 == 启用命令集合", [r["id"] for r in rows] == CM.ENABLED, str([r["id"] for r in rows]))
    except AssertionError as exc:
        rows = []
        ok("node 打桩可跑", False, str(exc))
    for r in rows:
        ok("命令 %s 生效" % r["id"], r["pass"], r.get("error") or r.get("rec") or "")

    print("结论:%s(%d 例,%d 失败)" % ("PASS" if FAIL == 0 else "FAIL", PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
