#!/usr/bin/env python3
"""`site_work_cmds.CMDS_JS` 的 **行为** 自检(node 打桩 window / document / __work)。

逐条实跑 16 条启用命令:用一个最小 DOM + `window.__work` 桩载入**真** `CMDS_JS`,
模拟点击 `.cmd`,断言每条都改变了可观测状态(side/split/panel/scope/unread 或
点击 / 派发 / 剪贴板记录)。点了不改变状态的命令在这里就会 FAIL。

注意:Windows 上不能把 JS 经进程替换喂给 node(拿到的是 `F:\\proc\\…` 管道路径,原生
win32 的 node 读不了),故统一写临时文件。由 `selftest_panels.py` 调用。
单跑:cd 本目录 && PYTHONIOENCODING=utf-8 python -B selftest_panels_js.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import site_work_cmds as C

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HARNESS = r"""
"use strict";
var rec = [];
function El(id, attrs) { this.id = id; this.a = attrs || {}; this.__h = {}; }
El.prototype.getAttribute = function (k) { return Object.prototype.hasOwnProperty.call(this.a, k) ? String(this.a[k]) : null; };
El.prototype.setAttribute = function (k, v) { this.a[k] = String(v); };
El.prototype.focus = function () { doc.activeElement = this; };
El.prototype.click = function () { rec.push("click:" + (this.id || "el")); };
El.prototype.querySelector = function (sel) { return sel.indexOf("cmd-name") >= 0 ? nameEl : null; };
El.prototype.querySelectorAll = function () { return []; };

var doc, els, groups, items, nameEl, state, W, actCmds;
function def(k, v) { Object.defineProperty(globalThis, k, { value: v, configurable: true, writable: true }); }
function reset() {
  rec = []; state.side = true; state.split = false; state.panel = "files";
  state.unread = false; state.scope = ""; els["act-theme"].clicks = 0;
  groups.forEach(function (g) { g.setAttribute("aria-expanded", "true"); });
}
function click(id) {
  els["cmds-list"].__h.click({ target: { closest: function (sel) {
    return sel === ".cmd" ? { getAttribute: function () { return id; }, disabled: false } : null; } } });
}
function has(p) { return rec.some(function (r) { return r.indexOf(p) === 0; }); }

els = { "cmds-list": new El("cmds-list"), "act-theme": new El("act-theme"), "clear2": new El("clear2") };
els["act-theme"].clicks = 0;
els["clear2"].click = function () { rec.push("click:clear2"); };
groups = [new El("g1", { "aria-expanded": "true" }), new El("g2", { "aria-expanded": "true" })];
items = [new El("i1", { "data-key": "k1", "data-count": "0" })];
nameEl = { textContent: "只看未完成" };
actCmds = new El("act", { "data-panel": "commands" });
state = { focus: 1, g: { 1: ["k1"], 2: [] }, side: true, split: false, panel: "files", unread: false, scope: "", act: { 1: "k1", 2: null } };
doc = { activeElement: null, body: {},
  getElementById: function (id) { return els[id] || null; },
  querySelector: function (sel) { return sel.indexOf('act[data-panel="commands"]') >= 0 ? actCmds : null; },
  querySelectorAll: function () { return []; },
  createElement: function () { return new El("tmp"); },
  dispatchEvent: function (ev) { rec.push("key:" + ev.key + (ev.ctrlKey ? ":ctrl" : "") + (ev.shiftKey ? ":shift" : "")); return true; },
  addEventListener: function () {} };
def("document", doc);
def("KeyboardEvent", function (t, i) { this.type = t; for (var k in i) { this[k] = i[k]; } });
def("location", { href: "file:///index.html" });
def("navigator", { clipboard: { writeText: function (u) { rec.push("clipboard:" + u); return {}; } } });
def("localStorage", { getItem: function () { return null; }, setItem: function () {} });
def("window", globalThis);
W = { state: state,
  qa: function (sel) {
    if (sel.indexOf(".tree-group") >= 0) { return groups; }
    if (sel.indexOf(".tree-item") >= 0) { return items; }
    return [];
  },
  on: function (el, t, fn) { if (el) { el.__h[t] = fn; } },
  empty: function (g) { rec.push("W.empty:" + g); },
  close: function (k) { rec.push("W.close:" + k); },
  setSide: function (v) { state.side = v; rec.push("W.setSide:" + v); },
  setSplit: function (v) { state.split = v; rec.push("W.setSplit:" + v); },
  setPanel: function (p) { state.panel = p; rec.push("W.setPanel:" + p); },
  onlyUnread: function (v) { state.unread = v; rec.push("W.onlyUnread:" + v); },
  searchScope: function (s) { state.scope = s; state.panel = "search"; rec.push("W.searchScope:" + s); } };
window.__work = W;
window.__INDEX__ = [];
window.__counts = { clear: function () { rec.push("counts.clear"); }, get: function () { return { count: 0 }; } };
require(process.argv[2]);   /* 载入真实 CMDS_JS(分派经 window.__work) */

/* 每条命令:pre 制造初始差异 -> click -> check 断言状态确实变了 */
var PRE = {
  "files": function () { state.panel = "search"; },
  "expand-all": function () { groups.forEach(function (g) { g.setAttribute("aria-expanded", "false"); }); },
  "clear-filters": function () { state.unread = true; }
};
var CHK = {
  "theme": function () { return has("click:act-theme"); },
  "welcome": function () { return has("W.empty:") && has("W.close:"); },
  "side": function () { return state.side === false; },
  "split": function () { return state.split === true; },
  "files": function () { return state.panel === "files"; },
  "search": function () { return state.panel === "search" && state.scope === "all"; },
  "goto": function () { return has("key:p:ctrl"); },
  "palette": function () { return has("key:p:ctrl:shift"); },
  "copy-link": function () { return rec.some(function (r) { return r.indexOf("clipboard:") === 0 && r.indexOf("#k1") >= 0; }); },
  "clear-counts": function () { return has("counts.clear"); },
  "collapse-all": function () { return groups.every(function (g) { return g.getAttribute("aria-expanded") === "false"; }); },
  "expand-all": function () { return groups.every(function (g) { return g.getAttribute("aria-expanded") === "true"; }); },
  "only-unread": function () { return state.unread === true && nameEl.textContent === "显示全部"; },
  "clear-filters": function () { return has("click:clear2") && state.unread === false; },
  "scope-all": function () { return state.scope === "all" && state.panel === "search"; },
  "scope-course": function () { return state.scope === "course" && state.panel === "search"; }
};
var ids = __IDS__, out = [];
ids.forEach(function (id) {
  reset();
  if (PRE[id]) { PRE[id](); }
  click(id);
  var pass = false, err = "";
  try { pass = CHK[id] ? CHK[id]() === true : false; if (!CHK[id]) { err = "缺少 CHK 用例"; } }
  catch (e) { err = String((e && e.message) || e); }
  out.push({ id: id, pass: pass, error: err, rec: rec.join("|") });
});
process.stdout.write(JSON.stringify(out) + "\n");
"""


def run_cmd_probes() -> list[dict]:
    """把 CMDS_JS 与打桩脚本写进临时目录跑一遍 node,返回每条命令的结果。"""
    node = shutil.which("node")
    assert node, "找不到 node,无法验证 CMDS_JS 行为"
    with tempfile.TemporaryDirectory(prefix="cmds-js-") as tmp:
        js = Path(tmp) / "cmds.js"
        js.write_text(C.CMDS_JS, encoding="utf-8")
        harness = Path(tmp) / "harness.js"
        harness.write_text(HARNESS.replace("__IDS__", json.dumps(C.ENABLED)), encoding="utf-8")
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
        rows = run_cmd_probes()
    except AssertionError as exc:
        print("FAIL", exc)
        print("结论:FAIL(0/1)")
        return 1
    ids = [r["id"] for r in rows]
    assert ids == C.ENABLED, "打桩命令集合与 CMDS 启用集不一致:%s" % ids
    bad = [r for r in rows if not r["pass"]]
    for r in rows:
        print("%s %s%s" % ("PASS" if r["pass"] else "FAIL", r["id"],
                           (" -> " + r["rec"]) if r["pass"] else (" -> " + (r["error"] or r["rec"]))))
    print("结论:%s(%d/%d 生效)" % ("PASS" if not bad else "FAIL", len(rows) - len(bad), len(rows)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
