#!/usr/bin/env python3
"""笔记正文惰性 `<template>` 自检:静态(在 template、不在实时 DOM、key 对齐)+ 行为(node 打桩)。

行为侧用最小 DOM + `window.__work` 桩载入**真** `site_work_note.NOTE_TPL_JS`,两条用例:
  1. 首次打开:`instantiateNote(key, host)` 把模板内容克隆成 `div.note-body.card-body[data-key]`
     塞进 host,默认 hidden,类名与结构正确
  2. **负向**:模板查不到(模拟 `data-key` 被改坏)-> 给「内容缺失」提示,不抛异常、不白屏

注意:Windows 上不能把 JS 经进程替换喂给 node(拿到 `F:\\proc\\…` 管道路径),故写临时文件。
由 `selftest_work.py` 调用。
单跑:cd 本目录 && PYTHONIOENCODING=utf-8 python -B selftest_notes.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import site_work_note as N

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOTE_TPL = re.compile(r'<template class="note-tpl" data-key="([^"]+)">')
LIVE_BODY = re.compile(r'class="note-body[^"]*" data-key="')

HARNESS = r"""
"use strict";
function El(tag, cls) { this.tag = tag; this.className = cls || ""; this.a = {}; this.children = []; this.hidden = true; this.textContent = ""; }
El.prototype.setAttribute = function (k, v) { this.a[k] = String(v); };
El.prototype.getAttribute = function (k) { return Object.prototype.hasOwnProperty.call(this.a, k) ? this.a[k] : null; };
El.prototype.appendChild = function (e) { this.children.push(e); return e; };
function def(k, v) { Object.defineProperty(globalThis, k, { value: v, configurable: true, writable: true }); }
var mode = "ok";
var frag = new El("#fragment", "");
frag.appendChild(new El("p", "prose-p"));
var tpl = { content: { cloneNode: function () { return frag; } } };
var doc = {
  createElement: function (tag) { return new El(tag); },
  querySelector: function (sel) { return mode === "bad" ? null : (sel.indexOf("note-tpl") >= 0 ? tpl : null); },
  addEventListener: function () {}
};
def("document", doc);
def("window", globalThis);
window.__work = { esc: function (s) { return String(s); } };
require(process.argv[2]);   /* 载入真实 NOTE_TPL_JS */

var out = [];
function probe(name, m, key, wantTpl) {
  mode = m;
  var host = new El("div", "group-body"), nb = null, err = "";
  try { nb = window.__work.instantiateNote(key, host); } catch (e) { err = String((e && e.message) || e); }
  var child = nb && nb.children[0], pass = false;
  if (wantTpl) {
    pass = !err && !!nb && nb.className === "note-body card-body" && nb.getAttribute("data-key") === key
      && nb.hidden === true && host.children.length === 1 && !!child && child.tag === "#fragment";
  } else {
    pass = !err && !!nb && nb.className === "note-body card-body" && nb.hidden === true
      && host.children.length === 1 && !!child && child.className === "note-missing"
      && String(child.textContent).indexOf("内容缺失") === 0;
  }
  out.push({ case: name, pass: pass, error: err, rec: nb ? nb.className + "|" + (child ? child.className : "none") : "none" });
}
probe("首次实例化克隆正文", "ok", "k1", true);
probe("坏 data-key 走内容缺失兜底", "bad", "k1", false);
process.stdout.write(JSON.stringify(out) + "\n");
"""


def run_probes() -> list[dict]:
    """把 NOTE_TPL_JS 与打桩脚本写进临时目录跑一遍 node,返回两条用例结果。"""
    node = shutil.which("node")
    assert node, "找不到 node,无法验证 NOTE_TPL_JS 行为"
    with tempfile.TemporaryDirectory(prefix="note-js-") as tmp:
        js = Path(tmp) / "note.js"
        js.write_text(N.NOTE_TPL_JS, encoding="utf-8")
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


def run(page: str, entries: list[dict], ok) -> None:
    """静态断言(渲染层)+ 行为断言(node 打桩);由 selftest_work 调用。"""
    body_slugs = {e["slug"] for e in entries if e["kind"] == "note" and e.get("body")}
    tpls = NOTE_TPL.findall(page)
    ok("笔记正文在 template,不在实时 DOM", not LIVE_BODY.search(page))
    ok("template 数 == 有正文笔记数", len(tpls) == len(body_slugs), "%d vs %d" % (len(tpls), len(body_slugs)))
    ok("template data-key == 有正文笔记 slug", set(tpls) == body_slugs,
       str(sorted(set(tpls) ^ body_slugs)[:3]))
    try:
        rows = run_probes()
    except AssertionError as exc:
        ok("笔记实例化 node 打桩可跑", False, str(exc))
        return
    for r in rows:
        ok("笔记实例化:%s" % r["case"], r["pass"], r.get("error") or r.get("rec") or "")


if __name__ == "__main__":
    rows = run_probes()
    bad = [r for r in rows if not r["pass"]]
    for r in rows:
        print("%s %s%s" % ("PASS" if r["pass"] else "FAIL", r["case"],
                           (" -> " + r["rec"]) if r["pass"] else (" -> " + (r["error"] or r["rec"]))))
    print("结论:%s(%d/%d 生效)" % ("PASS" if not bad else "FAIL", len(rows) - len(bad), len(rows)))
    sys.exit(0 if not bad else 1)
