#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第二段(侧栏 / 树键盘 / 主题 + 分屏 / 拖拽)。

本段管侧栏(活动栏 / 面板 / 树键盘 / 主题同步)与分屏(`Ctrl+\\` 拆分合并)。第四段
(`site_work_drag_js.DRAG_JS`,拖动标签换组)与第五段(`site_work_resize_js.RESIZE_JS`,
侧栏拖拽宽度)各自成自足 IIFE,拼在本段之后;三段经 `window.__work` 协作:本段用第一段的
`qa/on/open/save/render/activate/move/empty/state/group`,并暴露 `setSide/setPanel/syncTheme/
setSplit` 供第一段调用;末尾调用 `W.boot()` 触发首屏还原(此时侧栏函数已就绪)。

**分屏前置**:`window.innerWidth >= 1024` 才允许拆(设计 §8);不足时 `setSplit(true)`
不改状态,并弹 `.work-toast` 一句提示(不静默失败)。零外部资源、IIFE、无 eval;契约见
`site_dom.CONTRACT`。
"""

from site_work_drag_js import DRAG_JS
from site_work_filter import FILTER_JS
from site_work_resize_js import RESIZE_JS

_SPLIT = r"""
/* 工作台·第二段:侧栏(活动栏 / 树键盘 / 主题)+ 分屏(两组 / 拖拽)。 */
(function () {
  "use strict";
  var W = window.__work, doc = document;
  if (!W || !W.state) return;
  var S = W.state, qa = W.qa, on = W.on;
  var PANELS = ["files", "search", "commands"];
  var sidebar = doc.querySelector(".sidebar"), sideTree = doc.querySelector(".side-tree");
  var sideQ = doc.getElementById("side-q"), groupsEl = doc.querySelector(".groups");
  var stSplit = doc.querySelector(".st-split"), stTheme = doc.querySelector(".st-theme");
  /* ===== 侧栏 / 面板 / 主题 ===== */
  function isMobile() { return !!(window.matchMedia && matchMedia("(max-width:768px)").matches); }
  function syncMask() {   /* ★ 抽屉打开且 ≤768px 才出遮罩;桌面侧栏常驻,永不出遮罩 */
    var mk = doc.querySelector(".side-mask");
    if (mk) mk.classList.toggle("show", !!S.side && isMobile());
  }
  function setSide(open, persist) {
    S.side = !!open;
    if (sidebar) sidebar.setAttribute("data-open", S.side ? "true" : "false");
    var mb = doc.getElementById("menu"); if (mb) mb.setAttribute("aria-expanded", S.side ? "true" : "false");
    syncMask();
    if (persist !== false) W.save();
  }
  function setPanel(name, persist) {
    if (PANELS.indexOf(name) < 0) return;
    S.panel = name;
    if (sidebar) sidebar.setAttribute("data-panel", name);
    qa(".act[data-panel]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-panel") === name ? "true" : "false"); });
    if (name !== "files") setSide(true, false);
    if (persist !== false) W.save();
  }
  function syncTheme() {
    var dark = doc.documentElement.getAttribute("data-theme") === "dark";
    qa("#theme,#act-theme").forEach(function (b) { b.setAttribute("aria-pressed", dark ? "true" : "false"); b.title = dark ? "切换到亮色主题" : "切换到暗色主题"; });
    if (stTheme) stTheme.textContent = dark ? "深色" : "浅色";
  }
  function toggleTheme() {
    var next = doc.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    doc.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("note-theme", next); } catch (e) {}
    syncTheme(); W.save();
  }
  W.setSide = setSide; W.setPanel = setPanel; W.syncTheme = syncTheme;
  qa(".act[data-panel]").forEach(function (b) { on(b, "click", function () {
    var name = b.getAttribute("data-panel");
    if (name === S.panel && S.side) { setSide(false); return; }   /* 点当前面板 -> 收起侧栏 */
    setPanel(name);
    if (!S.side) setSide(true, false);   /* 收起时点任一面板 -> 展开 */
  }); });
  on(doc.getElementById("menu"), "click", function () { setSide(!S.side); });
  on(doc.querySelector(".side-mask"), "click", function () { setSide(false); });
  if (window.matchMedia) { try { matchMedia("(max-width:768px)").addEventListener("change", syncMask); } catch (e) {} }
  on(doc.getElementById("act-theme"), "click", toggleTheme);
  on(doc.getElementById("theme"), "click", function () { setTimeout(function () { syncTheme(); W.save(); }, 0); });
  on(sideTree, "click", function (e) {
    var gh = e.target.closest ? e.target.closest(".tree-group") : null;
    if (gh) { gh.setAttribute("aria-expanded", gh.getAttribute("aria-expanded") === "false" ? "true" : "false"); return; }
    var it = e.target.closest ? e.target.closest(".tree-item") : null;
    if (it) W.open(it.getAttribute("data-key"), S.focus);
  });
  on(sideTree, "keydown", function (e) {   /* 树键盘:↑↓ 移动 / ←→ 折叠展开 / Enter 打开 */
    var el = e.target.closest ? e.target.closest(".tree-item,.tree-group") : null;
    if (!el) return;
    var k = e.key, gh = el.classList.contains("tree-group") ? el : null;
    if (k === "ArrowDown" || k === "ArrowUp") {
      var v = qa(".tree-item", sideTree).filter(function (i) { return i.offsetParent !== null; });
      if (!v.length) return;
      var i = v.indexOf(doc.activeElement), d = k === "ArrowDown" ? 1 : -1;
      v[i < 0 ? (d > 0 ? 0 : v.length - 1) : Math.min(v.length - 1, Math.max(0, i + d))].focus();
      e.preventDefault(); return;
    }
    if (!gh && (k === "ArrowLeft" || k === "ArrowRight")) {
      var gh0 = el.parentElement.parentElement.previousElementSibling;
      if (gh0 && gh0.classList.contains("tree-group")) gh = gh0;
    }
    if (!gh) { if (k === "Enter" || k === " ") { e.preventDefault(); W.open(el.getAttribute("data-key"), S.focus); } return; }
    if (k === "ArrowRight") gh.setAttribute("aria-expanded", "true");
    else if (k === "ArrowLeft") gh.setAttribute("aria-expanded", "false");
    else if (k === "Enter" || k === " ") gh.setAttribute("aria-expanded", gh.getAttribute("aria-expanded") === "false" ? "true" : "false");
    else return;
    e.preventDefault();
  });
  on(doc, "keydown", function (e) {   /* Ctrl+B 侧栏 / Ctrl+K 侧栏搜索 */
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    var k = (e.key || "").toLowerCase();
    if (k === "b") { e.preventDefault(); setSide(!S.side); }
    else if (k === "k") { e.preventDefault(); setPanel("search"); if (sideQ) { sideQ.focus(); sideQ.select(); } }
  });
  /* ===== 分屏:两组上限;Ctrl+\ 拆分合并;宽 <1024 禁用(给提示,不静默失败) ===== */
  function canSplit() { return window.innerWidth >= 1024; }
  function toast(msg) {
    var t = doc.getElementById("work-toast");
    if (!t) {
      t = doc.createElement("div"); t.id = "work-toast"; t.className = "work-toast";
      t.setAttribute("role", "status"); t.hidden = true; doc.body.appendChild(t);
    }
    t.textContent = msg; t.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.hidden = true; }, 2600);
  }
  function setSplit(on, quiet) {   /* 拆分:露出第二组;合并:标签并回第一组(去重)并收起 */
    if (on && !canSplit()) {   /* ★ 宽 <1024:不拆,并给一句人话 */
      S.split = false;
      if (groupsEl) groupsEl.setAttribute("data-split", "false");
      if (stSplit) stSplit.textContent = "单栏";
      if (!quiet) toast("窗口宽度不足 1024px,已禁用分屏");
      return;
    }
    S.split = !!on;
    if (groupsEl) groupsEl.setAttribute("data-split", S.split ? "true" : "false");
    if (stSplit) stSplit.textContent = S.split ? "双栏" : "单栏";
    var g2 = W.group(2);   /* ★ 组 2 的 hidden 必须随分栏显隐,只靠 data-split 的 CSS 不够 */
    if (g2) {
      g2.hidden = !S.split;
      var gt = g2.querySelector(".group-tabs");
      if (gt) gt.hidden = !S.split;
    }
    if (S.split) {
      if (S.act[2] && S.g[2].indexOf(S.act[2]) >= 0) W.activate(S.act[2], 2); else W.empty(2);
    } else {
      var moved = S.g[2];
      S.g[2] = []; S.act[2] = null;
      moved.forEach(function (k) { if (S.g[1].indexOf(k) < 0) S.g[1].push(k); });
      W.render(1); W.render(2);
      if (S.act[1]) W.activate(S.act[1], 1); else W.empty(1);
    }
    if (!quiet) W.save();
  }
  W.setSplit = setSplit;
  on(doc, "keydown", function (e) {
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    if (e.key === "\\" || e.code === "Backslash") { e.preventDefault(); setSplit(!S.split); }
  }, true);
  W.boot();   /* boot 内会调 W.setSplit 把布局里的分栏状态落到 DOM */
  /* ★ 手机首次打开(无保存布局)默认收起抽屉;有保存布局则以保存值为准 */
  (function () {
    var saved = false;
    try { saved = !!localStorage.getItem("note:layout"); } catch (e) {}
    if (!saved && isMobile()) setSide(false, false);
  })();
})();
"""

SPLIT_JS = _SPLIT + "\n" + DRAG_JS + "\n" + RESIZE_JS + "\n" + FILTER_JS
