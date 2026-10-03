#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第二段(侧栏 / 树键盘 / 主题 + 分屏 / 拖拽)。

由 `site_work_js.WORK_JS` 拼在第一段(标签 / 布局记忆)之后、第三段
(`site_work_filter.FILTER_JS`,侧栏树过滤 + 卡片筛选)之前执行。拆段是为守住
「每个 .py ≤ 200 行」。本段管侧栏(活动栏 / 面板 / 树键盘 / 主题同步)与分屏
(`Ctrl+\\` 拆分合并、拖动标签换组,落点提示,源组空了即消失;拖拽落点样式在
`site_work_css.WORK_CSS`)。

三段经 `window.__work` 协作:本段用第一段的 `qa/on/open/save/render/activate/move/
empty/state/group`,并暴露 `setSide/setPanel/syncTheme/setSplit` 供第一段调用;末尾调用
`W.boot()` 触发首屏还原(此时侧栏函数已就绪)。零外部资源、IIFE、无 eval;契约见
`site_dom.CONTRACT`。
"""

from site_work_filter import FILTER_JS

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
  qa(".act[data-panel]").forEach(function (b) { on(b, "click", function () { setPanel(b.getAttribute("data-panel")); }); });
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
  /* ===== 分屏:两组上限;Ctrl+\ 拆分合并;拖动标签换组 ===== */
  function clearHint() { qa(".group.drop-target").forEach(function (x) { x.classList.remove("drop-target"); }); }
  function setSplit(on, quiet) {   /* 拆分:露出第二组;合并:标签并回第一组(去重)并收起 */
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
  var dragKey = null, dragFrom = 0;
  function targetGroup(e) {
    if (S.split) {
      var g = e.target && e.target.closest ? e.target.closest(".group") : null;
      return g ? parseInt(g.getAttribute("data-group"), 10) : 0;
    }
    var r = groupsEl.getBoundingClientRect();
    return e.clientX >= r.left + r.width / 2 ? 2 : 1;
  }
  on(groupsEl, "dragstart", function (e) {
    var cell = e.target && e.target.closest ? e.target.closest(".tab-cell") : null;
    var tab = cell && cell.querySelector(".tab");
    if (!tab) return;
    dragKey = tab.getAttribute("data-key");
    dragFrom = parseInt(cell.getAttribute("data-group") || "1", 10);
    cell.classList.add("dragging");
    if (e.dataTransfer) { e.dataTransfer.effectAllowed = "move"; try { e.dataTransfer.setData("text/plain", dragKey); } catch (x) {} }
  });
  on(groupsEl, "dragend", function (e) {
    var cell = e.target && e.target.closest ? e.target.closest(".tab-cell") : null;
    if (cell) cell.classList.remove("dragging");
    clearHint(); dragKey = null;
  });
  on(groupsEl, "dragover", function (e) {
    if (dragKey == null) return;
    e.preventDefault();
    var g = targetGroup(e);
    clearHint();
    if (!g || g === dragFrom) return;
    var el = W.group(g);
    if (el) el.classList.add("drop-target");
    if (e.dataTransfer) e.dataTransfer.dropEffect = "move";
  });
  on(groupsEl, "dragleave", function (e) { if (e.target === groupsEl) clearHint(); });
  on(groupsEl, "drop", function (e) {
    if (dragKey == null) return;
    e.preventDefault();
    var g = targetGroup(e), key = dragKey;
    clearHint(); dragKey = null;
    if (!g || g === dragFrom) return;
    W.move(key, dragFrom, g);   /* 源组空了由 W.move 收起(组 2)或回欢迎页(组 1) */
    if (!S.split && g === 2) setSplit(true, true);
    W.save();
  });
  W.boot();   /* boot 内会调 W.setSplit 把布局里的分栏状态落到 DOM */
  /* ★ 手机首次打开(无保存布局)默认收起抽屉;有保存布局则以保存值为准 */
  (function () {
    var saved = false;
    try { saved = !!localStorage.getItem("note:layout"); } catch (e) {}
    if (!saved && isMobile()) setSide(false, false);
  })();
})();
"""

SPLIT_JS = _SPLIT + "\n" + FILTER_JS
