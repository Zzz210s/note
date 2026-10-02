#!/usr/bin/env python3
"""0-Note 在线阅读站 · 计数(烘焙历史 + 浏览器本地增量)。

显示值 = 烘焙 count + 本地 add:烘焙值来自 `counts-seed.json`(生成站点时并入页面,
初值不随浏览器变),之后从站点打开课只写 localStorage,不回写文件、不上传。

只统计「从站点打开」的课;笔记不计数(笔记重分类与标签)。数据只在本地浏览器,
换设备/清缓存后增量归零,只剩烘焙历史。

join 一律走 `entry["path"]`:种子键是**仓库相对路径**,而页面侧条目 id 是 **slug**
(如 `0001-CLI-TUI-GUI`),两者不能直接相等 —— `bake()` 用条目清单换算,种子里没有
对应扫描条目的键(已退役、已改名)一律丢弃。

前端契约:页面里内联 `window.__COUNTS__`(字符串见 `seed_json()`)与 `COUNTS_JS`;
localStorage 键 `note:counts`,结构 `{"<slug>": {"add": n, "first": "...", "last": "..."}}`。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SEED_PATH = Path(__file__).resolve().parent / "counts-seed.json"


def load_seed() -> dict:
    """烘焙计数种子:仓库相对路径 -> {count, first, last}。

    文件缺失或坏掉时返回 `{}` 并打印一行提示,不抛异常(站点照常生成,烘焙按 0)。
    """
    try:
        raw = SEED_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError:
        print("计数种子缺失,烘焙值按 0 处理:" + str(SEED_PATH))
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print("计数种子解析失败,烘焙值按 0 处理:%s" % exc)
        return {}
    return data if isinstance(data, dict) else {}


def seed_json() -> str:
    """内联进 `<script>` 的烘焙 JSON。

    `<` 全部转义:`</script>` 会提前闭合脚本;`<!--` 实测安全无需处理(同 site_js)。
    """
    return json.dumps(load_seed(), ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def bake(entries: list[dict], seed: dict | None = None) -> dict:
    """并入条目清单:返回 `{slug: {count, first, last}}`,join 走 `entry["path"]`。

    页面侧标识是 slug、种子键是路径,故必须经条目清单换算;种子里有、清单里没有的
    键自然被丢弃(已退役的 `reference/` 速查卡、改过名的旧路径)。
    """
    seed = load_seed() if seed is None else seed
    out: dict[str, dict] = {}
    for e in entries:
        rec = seed.get(e.get("path"))
        if rec:
            out[e["slug"]] = {"count": rec.get("count", 0),
                              "first": rec.get("first", ""),
                              "last": rec.get("last", "")}
    return out


COUNTS_JS = r"""
/* 计数:显示 = 烘焙(window.__COUNTS__) + 本地增量(localStorage 键 note:counts)。
   inc 由工作台在「标签里首次打开该条目」时调用;get 只读,绝不自增。
   clear 只把本地增量归零,烘焙历史不动(命令面板「清空本地计数」)。 */
(function () {
  "use strict";
  var KEY = "note:counts", SEED = window.__COUNTS__ || {};
  function today() {
    var d = new Date();
    function p(n) { return (n < 10 ? "0" : "") + n; }
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  }
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  function save(store) {
    try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {}
  }
  /* get:烘焙 + 增量;增量 first/last 优先(更新),烘焙作兜底 */
  function get(key) {
    var baked = SEED[key] || null, rec = load()[key] || {add:0, first:"", last:""};
    return {
      count: (baked ? baked.count : 0) + (rec.add || 0),
      first: (baked && baked.first) || rec.first || "",
      last: rec.last || (baked && baked.last) || ""
    };
  }
  /* inc:只写本地增量;增量从 0 变 1 时才记 first */
  function inc(key) {
    var store = load(), rec = store[key] || {add:0, first:"", last:""};
    if (!rec.add) { rec.first = today(); }
    rec.add = (rec.add || 0) + 1;
    rec.last = today();
    store[key] = rec;
    save(store);
    return get(key);
  }
  /* clear:只把每条增量的 add 归零,first/last 与烘焙值都不动 */
  function clear() {
    var store = load();
    Object.keys(store).forEach(function (k) { store[k] = {add:0}; });
    save(store);
    return store;
  }
  window.__counts = {get: get, inc: inc, clear: clear};
})();
"""
