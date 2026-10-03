#!/usr/bin/env python3
"""`site_minify.py` 的自检:注释真删 / 内容不丢 / 行内 `//` 不动 / 压缩后 `node --check` 通过。

三条硬要求(简报 Task 9):
  1. CSS 块注释被删、声明内容不变(压缩前后去掉注释与空白后字符完全一致)
  2. **负向**:JS 字符串里的 `"http://a//b"` 与 `'// not a comment'` 必须原样保留
     —— 证明只删块注释与行首空白,不碰行内 `//`
  3. 压缩后 `node --check` 通过(拿真实内联段落逐段验,不只看玩具样例)
单跑:cd 本目录 && PYTHONIOENCODING=utf-8 python -B selftest_minify.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import site_counts
import site_js
import site_minify
import site_work_cmds
import site_work_js
import site_work_palette
import site_work_panels

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = FAIL = 0
COMMENT = re.compile(r"/\*.*?\*/", re.S)


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS", name)
    else:
        FAIL += 1
        print("FAIL", name, detail)


def node_check(js: str) -> tuple[int, str]:
    """写临时文件再 `node --check`(Windows 上进程替换的管道路径 node 读不了)。"""
    node = shutil.which("node")
    assert node, "找不到 node,无法校验 JS 语法"
    with tempfile.TemporaryDirectory(prefix="minify-check-") as tmp:
        p = Path(tmp) / "seg.js"
        p.write_text(js, encoding="utf-8")
        r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    return r.returncode, (r.stderr or "").strip()


def main() -> int:
    # 1. CSS:注释删净、声明原样、空行与行首缩进清零;内容(去空白后)一致
    css = "/* head */\n  .a{color:red}   /* tail */\n\n/* c */\n  .b { margin : 0 }\n"
    out = site_minify.minify_css(css)
    ok("CSS 块注释已删", "/*" not in out and "*/" not in out, out)
    ok("CSS 声明原样保留", ".a{color:red}" in out and ".b { margin : 0 }" in out, out)
    ok("CSS 空行清零", "\n\n" not in out)
    ok("CSS 行首缩进清零", all(not ln.startswith((" ", "\t")) for ln in out.split("\n")))
    ok("CSS 压缩前后去空白内容一致",
       "".join(COMMENT.sub("", css).split()) == "".join(out.split()), out)

    # 2. 负向:字符串 / 正则里的 `//` 与 `/*` 一律不动,只删块注释
    js = ('var a = "http://a//b";\n'
          "var b = '// not a comment';\n"
          'var c = 1; // 行内注释保留(本工具不删 //)\n'
          'var d = "/* not a comment */";\n'
          "var e = /([\"'])/g;\n"
          "/* real block comment */\n")
    mjs = site_minify.minify_js(js)
    ok("负向:双引号串里的 // 原样", '"http://a//b"' in mjs, mjs)
    ok("负向:单引号串里的 // 原样", "'// not a comment'" in mjs, mjs)
    ok("负向:字符串里的 /* */ 原样", '"/* not a comment */"' in mjs, mjs)
    ok("行内 // 注释保留(工具不处理)", "// 行内注释保留" in mjs, mjs)
    ok("真块注释已删", "real block comment" not in mjs, mjs)
    ok("JS 行首缩进清零", all(not ln.startswith((" ", "\t")) for ln in mjs.split("\n")))
    ok("负向样例压缩后 node --check", node_check(mjs)[0] == 0, node_check(mjs)[1][-200:])

    # 3. 真实内联段落:压缩后语法必须通过,且确实变小
    segs = {"WORK_JS": site_work_js.WORK_JS, "COUNTS_JS": site_counts.COUNTS_JS,
            "PANELS_JS": site_work_panels.PANELS_JS, "PALETTE_JS": site_work_palette.PALETTE_JS,
            "CMDS_JS": site_work_cmds.CMDS_JS, "site_js": site_js.JS,
            "WORK_BOOT": site_work_js.WORK_BOOT}
    for name, seg in segs.items():
        m = site_minify.minify_js(seg)
        rc, err = node_check(m)
        ok("%s 压缩后 node --check" % name, rc == 0, err[-200:])
        ok("%s 压缩后不更大" % name, len(m) <= len(seg), "%d -> %d" % (len(seg), len(m)))
    # 幂等:再压一次不再变(防止规则互相打架)
    ok("压缩幂等", site_minify.minify_js(site_minify.minify_js(site_work_js.WORK_JS)) == site_minify.minify_js(site_work_js.WORK_JS))

    print("结论:%s(%d 例,%d 失败)" % ("PASS" if FAIL == 0 else "FAIL", PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
