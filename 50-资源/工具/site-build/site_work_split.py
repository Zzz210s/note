#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第二段(侧栏 / 树 / 搜索 / 主题 + 分屏 / 拖拽)。

由 `site_work_js.WORK_JS` 拼在第一段(标签 / 布局记忆)之后执行。拆两段是为守住
「每个 .py ≤ 200 行」:第一段管标签与布局记忆,本段管侧栏(活动栏 / 面板 / 树键盘 /
搜索 / 主题同步)与分屏(`Ctrl+\\` 拆分合并、拖动标签换组,落点提示,源组空了即消失)。

两段经 `window.__work` 协作:本段用第一段的 `qa/on/norm/esc/open/save/render/activate/
move/state/group`,并暴露 `setSide/setPanel/syncTheme/setSplit` 供第一段调用;末尾调用
`W.boot()` 触发首屏还原(此时侧栏函数已就绪)。拖拽落点样式本段注入一条 `<style>`
(`site_work_css.WORK_CSS` 未含,不引外部资源;建议后续移回样式表)。
DOM/属性契约见 `site_dom.CONTRACT`;零外部资源、IIFE、无 eval、无内联事件属性。
"""

SPLIT_JS = r"""
/* 工作台·第二段:侧栏(活动栏 / 树 / 搜索 / 主题)+ 分屏(两组 / 拖拽)。 */
(function () {
  "use strict";
  var W = window.__work, doc = document;
  if (!W || !W.state) return;
  var S = W.state, qa = W.qa, on = W.on, norm = W.norm;
  var PANELS = ["files", "search", "commands"];
  var sidebar = doc.querySelector(".sidebar"), sideTree = doc.querySelector(".side-tree");
  var sideQ = doc.getElementById("side-q"), groupsEl = doc.querySelector(".groups");
  var stSplit = doc.querySelector(".st-split"), stTheme = doc.querySelector(".st-theme");
  /* ===== 侧栏 / 面板 / 主题 ===== */
  function setSide(open, persist) {
    S.side = !!open;
    if (sidebar) sidebar.setAttribute("data-open", S.side ? "true" : "false");
    var mb = doc.getElementById("menu"); if (mb) mb.setAttribute("aria-expanded", S.side ? "true" : "false");
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
  function filterTree(term) { term = norm(term); qa(".tree-item").forEach(function (it) { it.hidden = !!term && norm(it.textContent).indexOf(term) < 0; }); }
  function applyCards(term) {   /* 词 + 欢迎页 chip 双条件;与 site_js 的 chip 结果口径一致 */
    term = norm(term);
    var want = {}, shown = 0, cards = qa('.group-body[data-kind="welcome"] article.card');
    qa('.group-body[data-kind="welcome"] .chip').forEach(function (ch) {
      var g = ch.getAttribute("data-group") || "kind", v = ch.getAttribute("data-value") || "";
      if (ch.getAttribute("aria-pressed") === "true" && v) (want[g] = want[g] || []).push(v);
    });
    cards.forEach(function (c) {
      var ok = !term || norm(c.textContent).indexOf(term) >= 0;
      for (var g in want) { if (want[g].indexOf(c.getAttribute("data-" + g) || "") < 0) ok = false; }
      c.hidden = !ok;
      if (ok) shown++;
    });
    var on = !!term || Object.keys(want).length > 0, cnt = doc.getElementById("count"), emp = doc.getElementById("empty");
    if (cnt) cnt.textContent = on ? shown + " / " + cards.length + " 条" : "";
    if (emp) emp.hidden = shown !== 0;
  }
  W.setSide = setSide; W.setPanel = setPanel; W.syncTheme = syncTheme;
  qa(".act[data-panel]").forEach(function (b) { on(b, "click", function () { setPanel(b.getAttribute("data-panel")); }); });
  on(doc.getElementById("menu"), "click", function () { setSide(!S.side); });
  on(doc.querySelector(".side-mask"), "click", function () { setSide(false); });
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
  on(doc, "click", function (e) {   /* chip 之后按 词+chip 重算,盖过 site_js 的单词结果 */
    if (e.target.closest && e.target.closest('.group-body[data-kind="welcome"] .chip')) setTimeout(function () { applyCards(sideQ ? sideQ.value : ""); }, 0);
  });
  on(sideQ, "input", function () { filterTree(sideQ.value); applyCards(sideQ.value); });
  /* ===== 分屏:两组上限;Ctrl+\ 拆分合并;拖动标签换组 ===== */
  if (!doc.getElementById("work-drag-style")) {
    var tag = doc.createElement("style");
    tag.id = "work-drag-style";
    tag.textContent = "body.work .group.drop-target{outline:2px dashed var(--w-accent);outline-offset:-2px}" +
      "body.work .group.drop-target>.group-body{background:var(--w-accent-soft)}" +
      "body.work .tab-cell.dragging{opacity:.5}";
    (doc.head || doc.documentElement).appendChild(tag);
  }
  function clearHint() { qa(".group.drop-target").forEach(function (x) { x.classList.remove("drop-target"); }); }
  function setSplit(on, quiet) {   /* 合并时把第二组标签并回第一组(去重);拆分时空组给欢迎页 */
    S.split = !!on;
    if (groupsEl) groupsEl.setAttribute("data-split", S.split ? "true" : "false");
    if (stSplit) stSplit.textContent = S.split ? "双栏" : "单栏";
    if (S.split) {
      if (S.act[2] && S.g[2].indexOf(S.act[2]) >= 0) W.activate(S.act[2], 2);
    } else {
      var moved = S.g[2];
      S.g[2] = [];
      moved.forEach(function (k) { if (S.g[1].indexOf(k) < 0) S.g[1].push(k); });
      W.render(1); W.render(2);
      if (S.act[1]) W.activate(S.act[1], 1);
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
    W.move(key, dragFrom, g);
    if (!S.split && g === 2) setSplit(true, true);
    if (!S.g[dragFrom].length) {
      if (dragFrom === 2) setSplit(false);
      else if (dragFrom === 1) W.open("welcome", 1, true);
    }
    W.save();
  });
  W.boot();   /* boot 内会调 W.setSplit 把布局里的分栏状态落到 DOM */
})();
"""
