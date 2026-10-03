#!/usr/bin/env python3
"""`site_work_status.STATUS_JS` 的 **行为** 自检(node 打桩 window / document / __work)。

用最小 DOM + `window.__work` 桩载入**真** `STATUS_JS`,逐条调 `W.statusAct`:
六个已知动作各自改变可观测状态(close/empty、setPanel、onlyUnread、浮层、click、setSplit),
未知 `data-act` 走默认分支 —— 无副作用、不抛异常(简报硬要求)。

注意:Windows 上不能把 JS 经进程替换喂给 node(拿到 `F:\\proc\\…` 管道路径,原生 win32 的
node 读不了),故统一写临时文件。由 `selftest_work.py` 调用。
单跑:cd 本目录 && PYTHONIOENCODING=utf-8 python -B selftest_status_js.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import site_work_status as S

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ACTS = ["welcome", "open", "read", "thecount", "theme", "split"]

HARNESS = r"""
"use strict";
var rec = [], created = [];
function El(tag, cls) { this.tag = tag; this.className = cls || ""; this.a = {}; this.children = []; this.hidden = true; this.textContent = ""; }
El.prototype.setAttribute = function (k, v) { this.a[k] = String(v); };
El.prototype.getAttribute = function (k) { return Object.prototype.hasOwnProperty.call(this.a, k) ? this.a[k] : null; };
El.prototype.appendChild = function (e) { this.children.push(e); return e; };
El.prototype.click = function () { rec.push("click:" + (this.id || this.className || "el")); };
function def(k, v) { Object.defineProperty(globalThis, k, { value: v, configurable: true, writable: true }); }

var state = { focus: 1, g: { 1: ["k1"], 2: [] }, split: false, side: true, panel: "files", act: { 1: "k1", 2: null } };
var actTheme = new El("button", "act"); actTheme.id = "act-theme";
var body = { children: [], appendChild: function (e) { this.children.push(e); return e; } };
var doc = {
  activeElement: null, body: body,
  querySelector: function (sel) { return new El("span", sel.indexOf("st-") === 1 ? sel.slice(1) : "x"); },
  getElementById: function (id) { return id === "act-theme" ? actTheme : null; },
  createElement: function (tag) { var e = new El(tag); created.push(e); return e; },
  addEventListener: function () {}
};
def("document", doc);
def("window", globalThis);
function has(p) { return rec.some(function (r) { return r.indexOf(p) === 0; }); }
var W = {
  state: state, esc: function (s) { return String(s); },
  meta: function (key) { return { key: key, kind: "lesson", name: "测试课" }; },
  qa: function () { return []; },
  on: function (el, t, fn) { if (el) { el["on_" + t] = fn; } },
  close: function (k) { rec.push("W.close:" + k); },
  empty: function (g) { rec.push("W.empty:" + g); },
  setPanel: function (p) { state.panel = p; rec.push("W.setPanel:" + p); },
  onlyUnread: function (v) { rec.push("W.onlyUnread:" + v); },
  setSplit: function (v) { state.split = v; rec.push("W.setSplit:" + v); },
  syncTheme: function () { rec.push("W.syncTheme"); }
};
window.__work = W;
window.__counts = { get: function () { return { count: 3, first: "2026-01-01", last: "2026-01-02" }; } };
require(process.argv[2]);   /* 载入真实 STATUS_JS */

var CHK = {
  "welcome": function () { return has("W.close:k1") && has("W.empty:1"); },
  "open": function () { return has("W.setPanel:commands"); },
  "read": function () { return has("W.onlyUnread:true"); },
  "thecount": function (before) { var e = body.children[body.children.length - 1];
    return body.children.length > before && e && e.className === "st-pop" && e.hidden === false; },
  "theme": function () { return has("click:act-theme"); },
  "split": function () { return has("W.setSplit:true"); },
  "bogus": function (before) { return rec.length === 0 && body.children.length === before; }
};
var out = [];
["welcome", "open", "read", "thecount", "theme", "split", "bogus"].forEach(function (act) {
  rec = []; var before = body.children.length, pass = false, err = "";
  try { W.statusAct(act); pass = CHK[act](before) === true; }
  catch (e) { err = String((e && e.message) || e); }
  out.push({ act: act, pass: pass, error: err, rec: rec.join("|") });
});
process.stdout.write(JSON.stringify(out) + "\n");
"""


def run_probes() -> list[dict]:
    """把 STATUS_JS 与打桩脚本写进临时目录跑一遍 node,返回每条动作的结果。"""
    node = shutil.which("node")
    assert node, "找不到 node,无法验证 STATUS_JS 行为"
    with tempfile.TemporaryDirectory(prefix="status-js-") as tmp:
        js = Path(tmp) / "status.js"
        js.write_text(S.STATUS_JS, encoding="utf-8")
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
    assert payload is not None, "node 打桩没吐结果(rc=%s):%s" % (
        proc.returncode, (proc.stderr or "")[-400:])
    return payload


def main() -> int:
    try:
        rows = run_probes()
    except AssertionError as exc:
        print("FAIL", exc)
        print("结论:FAIL(0/1)")
        return 1
    acts = [r["act"] for r in rows]
    assert acts == ACTS + ["bogus"], "打桩动作集合变了:%s" % acts
    bad = [r for r in rows if not r["pass"]]
    for r in rows:
        print("%s %s%s" % ("PASS" if r["pass"] else "FAIL", r["act"],
                           (" -> " + r["rec"]) if r["pass"] else (" -> " + (r["error"] or r["rec"]))))
    print("结论:%s(%d/%d 生效)" % ("PASS" if not bad else "FAIL", len(rows) - len(bad), len(rows)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
