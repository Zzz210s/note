#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第一段(标签 / 布局记忆)。

`WORK_JS` = 本段 + `site_work_split.SPLIT_JS`(第二段:侧栏/树/搜索/主题 + 分屏/拖拽),
两段各自 IIFE,经 `window.__work` 协作;第一段只定义 `W.boot` 不调用,由第二段在
侧栏函数就绪后调用,触发首屏还原。

`WORK_BOOT` 是首屏单行 IIFE:渲染层必须内联在 `<head>`,先恢复主题再绘制(免首屏
闪烁),并把 `note:layout` 暂存到 `window.__workLayout`;标签等布局在 body 尾部脚本里
还原(尚未首绘,同样不闪)。课号 -> iframe 的 src 走 `window.__INDEX__` 的 `href`
(渲染层已 quote),`kind=course` 判为课。与 `site_js` 分工:欢迎页 chip 与 `#q` 搜索
仍由它管(工作台没有 `#q`);本工作台管外壳。
DOM/属性契约见 `site_dom.CONTRACT`;零外部资源、IIFE、无 eval、无内联事件属性。
"""
from site_work_split import SPLIT_JS
WORK_BOOT = (
    '(function(){try{var l=JSON.parse(localStorage.getItem("note:layout")||"null")||{};'
    'window.__workLayout=l;var t=l.theme;'
    'if(t!=="dark"&&t!=="light"){try{t=localStorage.getItem("note-theme")}catch(e){}}'
    'if(t!=="dark"&&t!=="light"){t=(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches)?"dark":"light"}'
    'document.documentElement.setAttribute("data-theme",t);'
    'if(l.theme==="dark"||l.theme==="light"){try{localStorage.setItem("note-theme",t)}catch(e){}}'
    '}catch(e){}})();'
)
_TAGS_JS = r"""
/* 工作台·第一段:标签 / 布局记忆(样式见 site_work_css,契约见 site_dom)。 */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement, W = window.__work = {};
  var LKEY = "note:layout", PANELS = ["files", "search", "commands"];
  var groupsEl = doc.querySelector(".groups"), stOpen = doc.querySelector(".st-open");
  var S = { g: { 1: [], 2: [] }, act: { 1: null, 2: null }, focus: 1, split: false, side: true, panel: "files", theme: null };
  var META = {}, ENT = {}, HREF2KEY = {};
  (Array.isArray(window.__INDEX__) ? window.__INDEX__ : []).forEach(function (e) {   /* kind:course -> 课 */
    if (!e || !e.anchor) return;
    ENT[e.anchor] = { kind: e.kind === "course" ? "lesson" : "note", href: e.href || "", name: e.title || e.anchor };
    if (e.href && e.href.charAt(0) !== "#") HREF2KEY[e.href] = e.anchor;
  });
  function qa(s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); }
  function on(el, t, fn, cap) { if (el) el.addEventListener(t, fn, cap); }
  function esc(s) { return (window.CSS && CSS.escape) ? CSS.escape(String(s)) : String(s).replace(/(["\\])/g, "\\$1"); }
  function norm(s) { s = s == null ? "" : String(s); return (s.normalize ? s.normalize("NFKC") : s).toLowerCase(); }
  function textOf(el) { return el && el.textContent ? el.textContent.trim() : ""; }
  function mk(tag, cls, at) { var e = doc.createElement(tag); e.className = cls; for (var k in at) e.setAttribute(k, at[k]); return e; }
  function metaOf(key) {   /* key -> {kind,name,href}:树项优先,其次 __INDEX__,欢迎页特判 */
    if (key === "welcome") return { key: key, kind: "welcome", name: "欢迎", href: "" };
    if (META[key]) return META[key];
    var it = doc.querySelector('.tree-item[data-key="' + esc(key) + '"]'), e = ENT[key];
    return (META[key] = { key: key, kind: (it && it.getAttribute("data-kind")) || (e && e.kind) || "note",
      name: textOf(it && it.querySelector(".t-name")) || (e && e.name) || key, href: e ? e.href : "" });
  }
  function groupEl(g) { return doc.querySelector('.group[data-group="' + g + '"]'); }
  function tabsBox(g) { var el = groupEl(g); return el ? el.querySelector(".group-tabs") : null; }
  function themeNow() { return root.getAttribute("data-theme") === "dark" ? "dark" : "light"; }
  /* 标签 = .tab-cell(标签按钮 + 关闭按钮;两者都 button,不嵌套) */
  function renderGroup(g) {
    var box = tabsBox(g);
    if (!box) return;
    qa(".tab-cell", box).forEach(function (c) { c.remove(); });
    S.g[g].forEach(function (key) {
      var m = metaOf(key), cell = mk("div", "tab-cell", { role: "presentation", "data-group": g });
      var tb = mk("button", "tab", { type: "button", role: "tab", "data-key": key, "data-kind": m.kind });
      var x = mk("button", "t-close", { type: "button", "aria-label": "关闭标签", "data-key": key, "data-group": g });
      cell.draggable = true;
      tb.appendChild(mk("span", "t-name", {})).textContent = m.name;
      cell.appendChild(tb); cell.appendChild(x); x.textContent = "\u00d7"; box.appendChild(cell);
    });
    syncTabs();
  }
  function syncTabs() {
    [1, 2].forEach(function (g) {
      var box = tabsBox(g), sel = S.act[g];
      if (box) qa(".tab", box).forEach(function (t) { t.setAttribute("aria-selected", t.getAttribute("data-key") === sel ? "true" : "false"); });
    });
  }
  function showKind(g, kind, href, key) {   /* 隐藏同组其它 .group-body;课写 src,笔记按 key 显隐 */
    var grp = groupEl(g), host = null;
    if (!grp) return;
    qa(".group-body", grp).forEach(function (b) { var hit = b.getAttribute("data-kind") === kind; if (hit && !host) host = b; b.hidden = !hit; });
    if (!host) return;
    if (kind === "lesson") {
      var f = host.querySelector("iframe.lesson-frame");
      if (f && href && f.getAttribute("src") !== href) f.setAttribute("src", href);
    } else if (kind === "note" && key) {
      var nb = host.querySelector('.note-body[data-key="' + esc(key) + '"]') || doc.querySelector('.note-body[data-key="' + esc(key) + '"]');
      if (nb) {
        if (nb.parentElement !== host) host.appendChild(nb);
        qa(".note-body", host).forEach(function (x) { x.hidden = x !== nb; });
        nb.hidden = false;
      }
    }
  }
  function count(key) {   /* 课首次打开 +1,并回填侧栏树次数 */
    if (!window.__counts || !window.__counts.inc) return;
    var rec = window.__counts.inc(key);
    if (!rec || typeof rec.count !== "number") return;
    qa('.tree-item[data-key="' + esc(key) + '"]').forEach(function (it) {
      it.setAttribute("data-count", rec.count);
      var c = it.querySelector(".t-count"); if (c) c.textContent = rec.count;
    });
  }
  function status() { if (stOpen) stOpen.textContent = "打开 " + (S.g[1].length + S.g[2].length); }
  function focusEditor(g) { var t = tabsBox(g); t = t && t.querySelector('.tab[aria-selected="true"]'); if (t) t.focus({ preventScroll: true }); }
  function currentTree(key) { qa(".tree-item").forEach(function (it) { it.setAttribute("aria-current", it.getAttribute("data-key") === key ? "true" : "false"); }); }
  function open(key, g, noFocus) {
    if (!key) return;
    g = g || S.focus || 1;
    if (S.g[g].indexOf(key) < 0) { S.g[g].push(key); renderGroup(g); if (metaOf(key).kind === "lesson") count(key); }
    activate(key, g); S.focus = g;
    if (!noFocus) focusEditor(g);
    status(); save();
  }
  function activate(key, g) {
    if (!g) g = S.focus;
    if (S.g[g].indexOf(key) < 0) return;
    S.act[g] = key; S.focus = g;
    var m = metaOf(key);
    showKind(g, m.kind, m.href, key); syncTabs(); currentTree(key); status();
  }
  function close(key, g) {
    g = g || S.focus;
    var list = S.g[g], i = list.indexOf(key);
    if (i < 0) return;
    list.splice(i, 1); S.act[g] = list[i] || list[i - 1] || null; renderGroup(g);
    if (!list.length) { if (g === 2 && W.setSplit) W.setSplit(false); else if (g === 1) open("welcome", 1, true); }
    else activate(S.act[g], g);
    status(); save();
  }
  function cycle() {
    var g = S.focus, list = S.g[g];
    if (list.length < 2) return;
    activate(list[(list.indexOf(S.act[g]) + 1) % list.length], g); focusEditor(g); save();
  }
  function move(key, from, to) {   /* 由第二段的拖拽调用 */
    if (from === to || S.g[from].indexOf(key) < 0) return;
    var a = S.g[from], i = a.indexOf(key);
    a.splice(i, 1);
    if (S.g[to].indexOf(key) < 0) S.g[to].push(key);
    S.act[from] = a[i] || a[i - 1] || null;
    renderGroup(from); renderGroup(to); activate(key, to); status();
  }
  function save() {
    try { localStorage.setItem(LKEY, JSON.stringify({ v: 1, g1: S.g[1], g2: S.g[2], act1: S.act[1], act2: S.act[2], focus: S.focus, split: S.split, side: S.side, panel: S.panel, theme: themeNow() })); } catch (e) {}
  }
  /* ===== 事件:标签 / 卡片 / 正文内链(侧栏与分屏见第二段) ===== */
  on(doc, "click", function (e) {
    var cell = e.target.closest ? e.target.closest(".tab-cell") : null;
    if (cell) {
      var g = parseInt(cell.getAttribute("data-group") || "1", 10), x = e.target.closest(".t-close"), t = e.target.closest(".tab");
      if (x) close(x.getAttribute("data-key"), g);
      else if (t) activate(t.getAttribute("data-key"), g);
      return;
    }
    var a = e.target.closest ? e.target.closest("a") : null;
    if (a) {
      var href = a.getAttribute("href") || "", key = href.charAt(0) === "#" ? href.slice(1) : HREF2KEY[href];
      if (key && (ENT[key] || doc.querySelector('.tree-item[data-key="' + esc(key) + '"]'))) { e.preventDefault(); open(key, S.focus); }
      return;
    }
    var card = e.target.closest ? e.target.closest("article.card[id]") : null;
    if (card) { e.preventDefault(); open(card.id, S.focus); }
  });
  on(doc, "auxclick", function (e) {   /* 中键关标签 */
    var t = e.button === 1 && e.target.closest ? e.target.closest(".tab") : null;
    if (t) { e.preventDefault(); close(t.getAttribute("data-key"), parseInt(t.closest(".tab-cell").getAttribute("data-group") || "1", 10)); }
  });
  on(doc, "keydown", function (e) {   /* Ctrl+W 关标签 / Ctrl+Tab 循环 */
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    if ((e.key || "").toLowerCase() === "w") { e.preventDefault(); if (S.act[S.focus]) close(S.act[S.focus], S.focus); }
    else if (e.key === "Tab") { e.preventDefault(); cycle(); }
  });
  on(doc, "keydown", function (e) {   /* 卡片上 Enter 开标签,不走 site_js 的新页 */
    if (e.key !== "Enter") return;
    var c = doc.activeElement && doc.activeElement.closest ? doc.activeElement.closest("article.card") : null;
    if (c) { e.preventDefault(); e.stopImmediatePropagation(); open(c.id, S.focus); }
  }, true);
  /* ===== 首屏还原(布局已由 WORK_BOOT 暂存到 window.__workLayout) ===== */
  function boot() {
    var l = window.__workLayout || {};
    if (l.theme === "dark" || l.theme === "light") S.theme = l.theme;
    S.side = l.side !== false;
    S.panel = PANELS.indexOf(l.panel) >= 0 ? l.panel : "files";
    S.g[1] = ["welcome"].concat((Array.isArray(l.g1) ? l.g1 : []).filter(function (k) { return k && k !== "welcome"; }));
    S.g[2] = Array.isArray(l.g2) ? l.g2.filter(Boolean) : [];
    S.act[1] = (l.act1 && S.g[1].indexOf(l.act1) >= 0) ? l.act1 : "welcome";
    S.act[2] = (l.act2 && S.g[2].indexOf(l.act2) >= 0) ? l.act2 : (S.g[2][0] || null);
    S.split = !!l.split;   /* 允许第二组暂时为空(拆栏后待拖入) */
    S.focus = l.focus === 2 ? 2 : 1;
    renderGroup(1); renderGroup(2); W.setSide(S.side, false); W.setPanel(S.panel, false); W.syncTheme();
    activate(S.act[1], 1);
    if (W.setSplit) W.setSplit(S.split, true);   /* 把布局里的分栏状态落到 DOM */
    status();
  }
  W.state = S; W.group = groupEl; W.qa = qa; W.on = on; W.esc = esc; W.norm = norm; W.save = save;
  W.render = renderGroup; W.activate = activate; W.open = open; W.close = close; W.move = move;
  W.boot = boot;   /* 由第二段在侧栏函数就绪后调用 */
})();
"""

WORK_JS = _TAGS_JS + "\n" + SPLIT_JS
