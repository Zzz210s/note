#!/usr/bin/env python3
"""0-Note 在线阅读站 · 快速打开(Ctrl+P)与命令面板(Ctrl+Shift+P)。

`window.__work` 就绪后由 `PALETTE_JS` 自建模态 DOM(契约见 `site_dom.CONTRACT` 的
「命令面板 / 快速打开」一段)并 append 到 body;面板样式也由它注入一段 `<style>`
(零外部资源:不是 `<link rel=stylesheet>`,也不是 `@import`)。渲染层不产出这段 DOM,
Task 9 只负责把 `PALETTE_JS` 内联进页面(**必须放在 `site_work_js.WORK_JS` 之后**,
否则 `window.__work` 还没有 open/close/state)。

打开条目一律走 `window.__work` 的 `open/close/empty/setSplit/setSide`,不另写一套标签
逻辑;清空计数走 `window.__counts.clear()`。零依赖、IIFE、无 eval、无内联事件、无 emoji。
"""
from __future__ import annotations

PALETTE_JS = r"""
/* 快速打开(Ctrl+P)与命令面板(Ctrl+Shift+P):自建模态,样式随本段注入。 */
(function () {
  "use strict";
  var doc = document, W = window.__work;
  if (!W || !W.open || !W.state) return;
  var S = W.state, on = W.on, qa = W.qa;
  var IDX = Array.isArray(window.__INDEX__) ? window.__INDEX__ : [];
  var BADGE = { course: "课程", know: "知识", project: "项目" };
  var STATUS = {}, PROJ = {}, HAY = {};
  function norm(s) { s = s == null ? "" : String(s); return (s.normalize ? s.normalize("NFKC") : s).toLowerCase(); }
  function el(tag, cls, at) { var e = doc.createElement(tag); if (cls) e.className = cls; for (var k in at) e.setAttribute(k, at[k]); return e; }
  function projOf(href) {   /* 笔记 href 是 #anchor,拿不到路径,故树名优先、路径兜底 */
    try { var p = decodeURIComponent(href || "").split("/");
      if (p[0] === "10-项目") return p[1] || "";
      return p[0] === "50-资源" ? "50-资源/" + (p[1] || "") : (p[0] || ""); } catch (e) { return ""; }
  }
  qa(".tree").forEach(function (tree) {   /* 项目名:侧栏树的分组名,第一处命中即项目组(标签组在后) */
    qa("li", tree).forEach(function (li) {
      var gh = li.querySelector(":scope > .tree-group"), nm = gh && gh.querySelector(".t-name");
      if (!gh || !nm) return;
      qa(":scope > ul > li > .tree-item[data-key]", li).forEach(function (it) {
        var k = it.getAttribute("data-key"); if (!(k in PROJ)) PROJ[k] = nm.textContent.trim();
      });
    });
  });
  IDX.forEach(function (e) {
    if (!e || !e.anchor) return;
    STATUS[e.anchor] = e.status || "";
    if (!(e.anchor in PROJ)) PROJ[e.anchor] = projOf(e.href);
    HAY[e.anchor] = norm([e.title, e.anchor, PROJ[e.anchor], e.summary, e.text].join(" "));
  });
  var pal = el("div", "palette", { id: "palette", role: "dialog", "aria-modal": "true", "aria-label": "快速打开", hidden: "" });
  var box = el("div", "palette-box", {});
  var input = el("input", "", { id: "palette-q", type: "text", role: "combobox", "aria-expanded": "false",
    "aria-controls": "palette-list", "aria-activedescendant": "", autocomplete: "off", "aria-label": "搜索条目" });
  var list = el("ul", "", { id: "palette-list", role: "listbox", "aria-label": "结果" });
  var hint = el("div", "palette-hint", {});
  box.appendChild(input); box.appendChild(list); box.appendChild(hint); pal.appendChild(box); doc.body.appendChild(pal);
  var CSS = ".palette{position:fixed;inset:0;z-index:200;display:flex;align-items:flex-start;justify-content:center;background:rgba(0,0,0,.28)}"
    + ".palette[hidden]{display:none!important}"
    + ".palette-box{margin-top:10vh;width:min(620px,92vw);max-height:72vh;display:flex;flex-direction:column;"
    + "background:var(--w-bg,#fff);color:var(--w-t1,#1f1f1f);border:1px solid var(--w-line,#d0d7de);"
    + "border-radius:8px;box-shadow:0 12px 40px rgba(0,0,0,.28);overflow:hidden}"
    + "#palette-q{flex:none;padding:10px 14px;border:0;border-bottom:1px solid var(--w-line,#d0d7de);"
    + "background:var(--w-input,transparent);color:inherit;font:inherit;outline:none}"
    + "#palette-list{margin:0;padding:4px;list-style:none;overflow:auto}"
    + "#palette-list li{display:flex;align-items:baseline;gap:8px;padding:6px 10px;border-radius:6px;cursor:pointer}"
    + "#palette-list li[aria-selected=true]{background:var(--w-accent-soft,rgba(0,95,184,.12))}"
    + "#palette-list .badge{flex:none;padding:0 4px;border-radius:3px;background:var(--w-hover,rgba(0,0,0,.05));font-size:10px}"
    + "#palette-list .p-name{font-size:14px}"
    + "#palette-list .p-proj,#palette-list .p-hint{margin-left:auto;color:var(--w-t2,#616161);font-size:12px}"
    + ".palette-hint{flex:none;padding:6px 12px;border-top:1px solid var(--w-line,#d0d7de);color:var(--w-t2,#616161);font-size:12px}";
  var style = el("style", "", {}); style.textContent = CSS; doc.head.appendChild(style);
  var mode = "goto", lastFocus = null, hi = -1, res = [], todoOn = false, hiddenBy = [];
  function row(e) { var t = e.kind && BADGE[e.kind] ? e.kind : "know";
    return { key: e.anchor, title: e.title || e.anchor, type: t, badge: BADGE[t], proj: PROJ[e.anchor] || "" }; }
  function score(e, q) {   /* 课号 > 标题 > 全文:子串优先,否则按顺序子序列兜底 */
    var k = norm(e.anchor), t = norm(e.title), h = HAY[e.anchor] || "", i;
    if ((i = k.indexOf(q)) >= 0) return 1000 - i;
    if ((i = t.indexOf(q)) >= 0) return 900 - i;
    if ((i = h.indexOf(q)) >= 0) return 500 - i;
    var j = 0;
    for (i = 0; i < h.length && j < q.length; i++) if (h.charAt(i) === q.charAt(j)) j++;
    return j === q.length ? 100 : 0;
  }
  function welcome() { var g = S.focus || 1; S.g[g].slice().forEach(function (k) { W.close(k, g); }); if (W.empty) W.empty(g); }
  function clearCounts() {
    if (window.__counts && window.__counts.clear) window.__counts.clear();
    qa(".tree-item[data-key]").forEach(function (it) {
      var k = it.getAttribute("data-key"), c = window.__counts && window.__counts.get ? window.__counts.get(k).count : 0;
      it.setAttribute("data-count", c); var n = it.querySelector(".t-count"); if (n) n.textContent = c;
    });
  }
  function copyLink() {
    var key = S.act[S.focus || 1]; if (!key) return;
    var url = location.href.split("#")[0] + "#" + encodeURIComponent(key);
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url)["catch"](function () {});
      else { var ta = doc.createElement("textarea"); ta.value = url; doc.body.appendChild(ta); ta.select(); doc.execCommand("copy"); ta.remove(); }
    } catch (e) {}
  }
  function toggleTodo() {
    todoOn = !todoOn;
    if (!todoOn) { hiddenBy.forEach(function (x) { x.hidden = false; }); hiddenBy = []; return; }
    hiddenBy = [];
    qa(".tree-item[data-key]").forEach(function (it) {
      if (STATUS[it.getAttribute("data-key")] === "done" && !it.hidden) { it.hidden = true; hiddenBy.push(it); }
    });
    qa('.group-body[data-kind="welcome"] article.card').forEach(function (c) {
      if (c.getAttribute("data-status") === "done" && !c.hidden) { c.hidden = true; hiddenBy.push(c); }
    });
  }
  var CMDS = [
    { label: "切换主题", hint: "浅色 / 深色", run: function () { var b = doc.getElementById("act-theme"); if (b) b.click(); } },
    { label: "打开欢迎页", hint: "清空当前组标签", run: welcome },
    { label: "收起侧栏", hint: "Ctrl+B", run: function () { if (W.setSide) W.setSide(false); } },
    { label: "清空本地计数", hint: "只清本地增量,烘焙保留", run: clearCounts },
    { label: "复制当前条目链接", hint: "当前组打开的条目", run: copyLink },
    { label: "只看未完成", hint: "过滤侧栏树与卡片", run: toggleTodo }
  ];
  function labelOf(c) { return c.label === "只看未完成" && todoOn ? "显示全部" : c.label; }
  function sync() {
    qa("li", list).forEach(function (li, i) { li.setAttribute("aria-selected", i === hi ? "true" : "false"); });
    input.setAttribute("aria-activedescendant", hi >= 0 ? "palette-opt-" + hi : "");
    var cur = list.children[hi];
    if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: "nearest" });
  }
  function render() {
    var q = norm(input.value).trim(); res = [];
    if (mode === "cmd") CMDS.forEach(function (c) { var lb = labelOf(c); if (!q || norm(lb).indexOf(q) >= 0) res.push({ cmd: c, label: lb }); });
    else if (!q) IDX.forEach(function (e) { if (e && e.anchor) res.push(row(e)); });
    else IDX.forEach(function (e) { if (!e || !e.anchor) return; var s = score(e, q); if (s > 0) { var r = row(e); r.s = s; res.push(r); } });
    if (mode !== "cmd" && q) res.sort(function (a, b) { return b.s - a.s; });
    res = res.slice(0, 60);
    if (hi < 0 || hi >= res.length) hi = res.length ? 0 : -1;
    list.textContent = "";
    res.forEach(function (r, i) {
      var li = el("li", "", { role: "option", id: "palette-opt-" + i, "aria-selected": i === hi ? "true" : "false" });
      if (mode === "cmd") {
        var l = el("span", "p-name", {}); l.textContent = r.label;
        if (r.cmd.hint) { var hh = el("span", "p-hint", {}); hh.textContent = r.cmd.hint; li.appendChild(l); li.appendChild(hh); }
        else li.appendChild(l);
      } else {
        var b = el("span", "badge", { "data-type": r.type }); b.textContent = r.badge;
        var n = el("span", "p-name", {}); n.textContent = r.title;
        var p = el("span", "p-proj", {}); p.textContent = r.proj;
        li.appendChild(b); li.appendChild(n); li.appendChild(p);
      }
      list.appendChild(li);
    });
    sync();
  }
  function open(m) {
    mode = m; lastFocus = doc.activeElement; input.value = ""; hi = -1;
    input.setAttribute("aria-label", m === "cmd" ? "命令" : "搜索条目");
    input.setAttribute("placeholder", m === "cmd" ? "输入命令…" : "搜索条目…");
    pal.setAttribute("aria-label", m === "cmd" ? "命令面板" : "快速打开");
    hint.textContent = m === "cmd" ? "↑↓ 选择 · Enter 执行 · Esc 关闭"
      : "↑↓ 选择 · Enter 当前组打开 · Ctrl+Enter 另一组打开 · Esc 关闭";
    pal.hidden = false; input.setAttribute("aria-expanded", "true");
    render(); input.focus();
  }
  function close() {
    if (pal.hidden) return;
    pal.hidden = true; input.setAttribute("aria-expanded", "false");
    var f = lastFocus; lastFocus = null;
    if (f && f.focus) { try { f.focus(); } catch (e) {} }
  }
  function choose(alt) {
    if (hi < 0 || !res[hi]) return;
    if (mode === "cmd") { var c = res[hi].cmd; close(); c.run(); return; }
    var key = res[hi].key, g = S.focus || 1, tgt = g === 1 ? 2 : 1;
    close();
    if (alt) { if (tgt === 2 && !S.split && W.setSplit) W.setSplit(true); W.open(key, tgt); }
    else W.open(key, g);
  }
  function move(d) { if (!res.length) return; hi = (hi + d + res.length) % res.length; sync(); }
  on(input, "input", render);
  on(input, "keydown", function (e) {
    var k = e.key;
    if (k === "ArrowDown") { e.preventDefault(); move(1); }
    else if (k === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (k === "Enter") { e.preventDefault(); choose(e.ctrlKey || e.metaKey); }
    else if (k === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
  });
  on(list, "click", function (e) {
    var li = e.target.closest ? e.target.closest("li") : null;
    if (!li) return;
    hi = Array.prototype.indexOf.call(list.children, li); choose(e.ctrlKey || e.metaKey);
  });
  on(pal, "mousedown", function (e) { if (e.target === pal) { e.preventDefault(); close(); } });
  on(doc, "keydown", function (e) {   /* 打开快捷键 + 聚焦陷阱(捕获,优于页面其它处理) */
    if (!pal.hidden) {
      if (e.key === "Tab") { e.preventDefault(); input.focus(); }
      else if (e.key === "Escape") { e.preventDefault(); close(); }
      return;
    }
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    var k = (e.key || "").toLowerCase(), code = e.code || "";
    if (k === "p" || code === "KeyP") { e.preventDefault(); e.stopPropagation(); open(e.shiftKey ? "cmd" : "goto"); }
  }, true);
  on(doc, "focusin", function (e) { if (!pal.hidden && !pal.contains(e.target)) input.focus(); });
})();
"""
