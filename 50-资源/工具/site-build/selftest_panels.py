#!/usr/bin/env python3
"""工作台面板自检:三个面板容器 / 搜索面板控件 / 命令条数 / PANELS_JS 语法 + 两条负向。

只读真实仓库与真实 `render_page` 产出,不写仓库文件(临时 JS 写在系统临时目录)。
跑法:`cd 50-资源/工具/site-build && PYTHONIOENCODING=utf-8 python -B selftest_panels.py`

口径(契约 `site_dom.CONTRACT`「工作台页」一段 + Task 2 简报):
  · `aside.sidebar` 下恰有三个 `.side-body[data-panel=files|search|commands]`,内容各不相同;
  · 搜索面板含 `#panel-q` / `#panel-scope` / `#panel-results` / `#panel-empty`;
  · 命令面板含 `#cmds-list` 且命令条数 ≥10;
  · `PANELS_JS` 无旧 beacon、无 `eval`、无 `innerHTML`(命中片段必须走 DOM API),
    且 `node --check` 通过(Windows 上用临时文件,不用会被 shell 吃掉的进程替换)。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import site_render
import site_scan
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

    # 3. 命令面板
    cmds = body_map(side).get("commands", "")
    ok("命令面板含 #cmds-list", 'id="cmds-list"' in cmds)
    n = cmds.count('data-cmd="')
    ok("命令条数 ≥10", n >= 10, "实际 %d" % n)

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

    print("结论:%s(%d 例,%d 失败)" % ("PASS" if FAIL == 0 else "FAIL", PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
