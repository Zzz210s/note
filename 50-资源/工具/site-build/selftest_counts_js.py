#!/usr/bin/env python3
"""`site_counts.COUNTS_JS` 的 **行为** 自检(node 打桩 window / localStorage)。

注意:不能把 `COUNTS_JS` 经进程替换喂给 node —— Windows 上 `node --check <(python …)`
拿到的是 `F:\\proc\\<pid>\\fd\\N` 管道路径,原生 win32 的 node 读不了。故统一写临时文件。

由 `selftest_counts.py` 汇总执行(它会把本模块的 `test_*` 一并跑);
单跑:cd 本目录 && PYTHONIOENCODING=utf-8 python -B selftest_counts_js.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import site_counts as C

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# node 侧用例名(集合相等即断言「覆盖项没被删掉」)
EXPECTED_CHECKS = {
    "get 连调两次不自增、且不写 localStorage",
    "inc 首次写 first(今天)、add=1",
    "inc 二次不改 first、只改 last",
    "clear 后烘焙值仍在、增量归零",
    "新条目 inc:无烘焙值也自洽",
    "localStorage 抛异常时不崩",
}

HARNESS = r"""
"use strict";
var store = Object.create(null);
var throwAll = false;
globalThis.window = globalThis;
globalThis.localStorage = {
  getItem: function (k) {
    if (throwAll) { throw new Error("storage blocked"); }
    return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null;
  },
  setItem: function (k, v) {
    if (throwAll) { throw new Error("storage blocked"); }
    store[k] = String(v);
  },
  removeItem: function (k) { delete store[k]; }
};
window.__COUNTS__ = {"0001-CLI-TUI-GUI": {count: 2, first: "2026-09-27", last: "2026-09-27"}};
require(process.argv[2]);
var c = window.__counts, results = [], KEY = "note:counts";

function check(name, fn) {
  try { fn(); results.push({name: name, pass: true}); }
  catch (e) { results.push({name: name, pass: false, error: String((e && e.message) || e)}); }
}
function eq(actual, expected, msg) {
  if (actual !== expected) {
    throw new Error(msg + "(实际 " + JSON.stringify(actual) + " != 期望 " + JSON.stringify(expected) + ")");
  }
}
function today() {
  var d = new Date();
  var p = function (n) { return (n < 10 ? "0" : "") + n; };
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
}
function rec(key) { return JSON.parse(store[KEY])[key]; }

check("get 连调两次不自增、且不写 localStorage", function () {
  var a = c.get("0001-CLI-TUI-GUI"), b = c.get("0001-CLI-TUI-GUI");
  eq(a.count, 2, "首次 get 应等于烘焙值");
  eq(b.count, 2, "重复 get 不得自增");
  eq(Object.keys(store).length, 0, "get 不得写 localStorage");
});

check("inc 首次写 first(今天)、add=1", function () {
  var r = c.inc("0001-CLI-TUI-GUI");
  eq(r.count, 3, "烘焙 2 + 增量 1;");
  eq(r.first, "2026-09-27", "显示 first 仍优先烘焙值;");
  eq(rec("0001-CLI-TUI-GUI").add, 1, "增量应为 1;");
  eq(rec("0001-CLI-TUI-GUI").first, today(), "首次 inc 应把今天写进 first;");
  eq(rec("0001-CLI-TUI-GUI").last, today(), "last 应为今天;");
});

check("inc 二次不改 first、只改 last", function () {
  var raw = JSON.parse(store[KEY]);
  raw["0001-CLI-TUI-GUI"].first = "2020-01-01";
  raw["0001-CLI-TUI-GUI"].last = "2020-01-02";
  store[KEY] = JSON.stringify(raw);
  var r = c.inc("0001-CLI-TUI-GUI");
  eq(rec("0001-CLI-TUI-GUI").first, "2020-01-01", "已有增量时不得改写 first;");
  eq(rec("0001-CLI-TUI-GUI").last, today(), "last 应更新为今天;");
  eq(rec("0001-CLI-TUI-GUI").add, 2, "增量应累加;");
  eq(r.count, 4, "烘焙 2 + 增量 2;");
});

check("clear 后烘焙值仍在、增量归零", function () {
  c.clear();
  var r = c.get("0001-CLI-TUI-GUI");
  eq(r.count, 2, "clear 后应回到烘焙值;");
  eq(r.first, "2026-09-27", "烘焙 first 不得被动;");
  eq(rec("0001-CLI-TUI-GUI").add, 0, "增量应归零;");
});

check("新条目 inc:无烘焙值也自洽", function () {
  var r = c.inc("0011-tmux");
  eq(r.count, 1, "无烘焙值时首次数为 1;");
  eq(r.first, today(), "first 为今天;");
  eq(r.last, today(), "last 为今天;");
});

check("localStorage 抛异常时不崩", function () {
  throwAll = true;
  eq(c.get("0001-CLI-TUI-GUI").count, 2, "读不到存储时退回烘焙值;");
  eq(c.inc("0001-CLI-TUI-GUI").count, 2, "写失败不抛异常,增量自然记不住;");
  c.clear();
});

var failed = results.filter(function (r) { return !r.pass; });
process.stdout.write(JSON.stringify({results: results, failed: failed.length}) + "\n");
process.exit(failed.length ? 1 : 0);
"""


def run_harness() -> list[dict]:
    """把 COUNTS_JS 与打桩脚本写进临时目录跑一遍 node,返回每条用例的结果。"""
    node = shutil.which("node")
    assert node, "找不到 node,无法验证 COUNTS_JS 行为"
    with tempfile.TemporaryDirectory(prefix="counts-js-") as tmp:
        js = Path(tmp) / "counts.js"
        js.write_text(C.COUNTS_JS, encoding="utf-8")
        harness = Path(tmp) / "harness.js"
        harness.write_text(HARNESS, encoding="utf-8")
        proc = subprocess.run([node, str(harness), str(js)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
    payload = None
    if lines:
        try:
            payload = json.loads(lines[-1])
        except ValueError:
            payload = None
    assert payload is not None, "node 打桩没吐出结果(rc=%s):%s" % (
        proc.returncode, (proc.stderr or "")[-400:])
    return payload["results"]


def test_js_behaviour():
    """node 打桩实跑:覆盖 get / inc / clear / 存储异常四条主链路。"""
    results = run_harness()
    names = {r["name"] for r in results}
    assert names == EXPECTED_CHECKS, "打桩用例集合变了,缺:%s 多:%s" % (
        EXPECTED_CHECKS - names, names - EXPECTED_CHECKS)
    bad = [r for r in results if not r["pass"]]
    assert not bad, "JS 行为失败:%s" % [(r["name"], r.get("error")) for r in bad]


def main() -> int:
    try:
        test_js_behaviour()
    except AssertionError as exc:
        print("FAIL test_js_behaviour ->", exc)
        print("结论:FAIL(1/1)")
        return 1
    print("PASS test_js_behaviour(%d 项 node 断言)" % len(EXPECTED_CHECKS))
    print("结论:PASS(1/1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
