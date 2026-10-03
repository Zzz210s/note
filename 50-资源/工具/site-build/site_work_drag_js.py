#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第四段(拖动标签换组)。

从 `site_work_split.SPLIT_JS` 拆出(该段加侧栏宽度与分屏守卫后触 200 行上限)。自足 IIFE:
只吃 `window.__work` 的 `state/qa/on/group/move/save/setSplit`,自己取 `.groups`。
落点提示样式(`.drop-target` / `.tab-cell.dragging`)在 `site_work_css.WORK_CSS`。

**宽 <1024 不是落点**:`targetGroup` 在未分屏且 `window.innerWidth < 1024` 时一律返回第 1 组
—— 否则标签会被拖进 `display:none` 的第二组,标签栏里凭空少一个(静默丢标签)。
两组的拆分 / 合并本身由 `site_work_split.setSplit` 把关(它才是唯一的拦截点)。
"""
from __future__ import annotations

DRAG_JS = r"""
/* 工作台·第四段:拖动标签换组(两组;宽 <1024 不分屏,右半区不再是落点)。 */
(function () {
  "use strict";
  var W = window.__work, doc = document;
  if (!W || !W.state) return;
  var S = W.state, on = W.on, groupsEl = doc.querySelector(".groups");
  if (!groupsEl) return;
  function canSplit() { return window.innerWidth >= 1024; }
  function clearHint() { W.qa(".group.drop-target").forEach(function (x) { x.classList.remove("drop-target"); }); }
  function targetGroup(e) {
    if (S.split) {
      var g = e.target && e.target.closest ? e.target.closest(".group") : null;
      return g ? parseInt(g.getAttribute("data-group"), 10) : 0;
    }
    if (!canSplit()) return 1;   /* ★ 宽 <1024 不分屏:右半区不再被当成第二组 */
    var r = groupsEl.getBoundingClientRect();
    return e.clientX >= r.left + r.width / 2 ? 2 : 1;
  }
  var dragKey = null, dragFrom = 0;
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
    if (!S.split && g === 2) W.setSplit(true, true);
    W.save();
  });
})();
"""
