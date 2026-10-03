#!/usr/bin/env python3
"""Task 8 自检:五档断点 / 分隔条契约 / 分屏前置 / 非法宽度回退(含一条 node 负向)。

由 `selftest_work.main()` 以 `run(ok)` 调用 —— 该文件已 186 行,直接加会破库规「每 .py ≤ 200 行」。
四条口径(简报 Step 1):
  1. 响应式 CSS 里出现 480 / 768 / 1024 / 1440 四个断点(逐个字符串),且该表确实拼进了 WORK_CSS
  2. 契约含 `.side-resizer[role=separator][aria-orientation=vertical]`
  3. `SPLIT_JS` 的分屏前置条件含 `innerWidth >= 1024`,并且 `setSplit` 真的用了它
  4. 负向:非法宽度(`"abc"` / 空串 / 越界 / `1e3`)被 `sideWidth` 回退 260 —— 真跑 node
单跑:cd 50-资源/工具/site-build && PYTHONIOENCODING=utf-8 python -B selftest_breakpoints.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import site_dom
import site_work_css
import site_work_resp_css
import site_work_resize_js
import site_work_split

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BREAKPOINTS = ["max-width:480px", "max-width:768px", "min-width:1024px", "min-width:1440px"]
WANT = {"abc": 260, "": 260, "150": 260, "500": 260, "1e3": 260, "-5": 260,
        "200": 200, "300": 300, "420": 420}


def widths() -> dict[str, int]:
    """把纯函数 sideWidth 写进临时文件跑 node(Windows 上不能把 JS 经管道喂给 node)。"""
    node = shutil.which("node")
    assert node, "找不到 node,无法验证 sideWidth 回退"
    cases = list(WANT)
    script = (site_work_resize_js.SIDE_WIDTH_JS + "\n"
              "process.stdout.write(JSON.stringify(process.argv.slice(2).map(sideWidth)));\n")
    with tempfile.TemporaryDirectory(prefix="side-width-") as tmp:
        p = Path(tmp) / "w.js"
        p.write_text(script, encoding="utf-8")
        r = subprocess.run([node, str(p), *cases], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    assert r.returncode == 0, "node 跑 sideWidth 失败:%s" % (r.stderr or "")[-300:]
    return dict(zip(cases, json.loads(r.stdout)))


def run(ok) -> None:
    css = site_work_resp_css.RESPONSIVE_CSS
    missing = [s for s in BREAKPOINTS if s not in css]
    ok("五档断点 480 / 768 / 1024 / 1440 逐个出现(RESPONSIVE_CSS)", not missing, "缺:%s" % missing)
    ok("响应式表拼进了 WORK_CSS,且在卡片表 PROJ_CSS 之后",
       site_work_css.WORK_CSS.count(css) == 1
       and site_work_css.WORK_CSS.index("minmax(260px,1fr)") < site_work_css.WORK_CSS.index(css))
    ok("契约含 .side-resizer[role=separator][aria-orientation=vertical]",
       ".side-resizer[role=separator][aria-orientation=vertical]" in site_dom.CONTRACT)
    js = site_work_split.SPLIT_JS
    ok("SPLIT_JS 分屏前置条件含 innerWidth >= 1024 且 setSplit 真的用它",
       "innerWidth >= 1024" in js and js.count("!canSplit()") >= 2, "canSplit 引用 %d 处" % js.count("canSplit"))
    got = widths()
    bad = {k: v for k, v in got.items() if v != WANT[k]}
    ok("负向:非法 / 越界宽度回退 260,合法值原样", not bad, "偏差:%s" % bad)


def main() -> int:
    n = 0

    def _ok(name: str, cond: bool, detail: str = "") -> None:
        nonlocal n
        n += 1
        print("%s %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else " " + detail))

    run(_ok)
    print("结论:PASS(%d 例)" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
