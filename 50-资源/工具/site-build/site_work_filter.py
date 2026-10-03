#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第三段(侧栏树过滤 + 卡片筛选)。

由 `site_work_split.SPLIT_JS` 拼在第二段之后(同一段内联脚本),IIFE 经 `window.__work`
取 `qa/on/norm/state`。工作台有三处筛选源,本段把它们汇总成一次重算:

  · `#side-q` 搜索词 —— 同时收侧栏树(`filterTree`)与条目卡(`applyCards`);
  · 欢迎页 chip —— `site_js` 的 chip 选择器只认欢迎页(由它切 aria-pressed),本段在其后延后重算;
  · 侧栏 chip —— `site_js` 不覆盖,由本段切 aria-pressed 并立即重算。

`#clear2` 口径 = **清空全部筛选**:欢迎页 chip 由 `site_js` 清,本段清侧栏 chip 与 `#side-q`,
并复位侧栏树与「只看未完成」(命令面板的 `W.onlyUnread`)。拆出本段只为守住库规
「每个 .py ≤ 200 行」。
"""

FILTER_JS = r"""
/* 工作台·第三段:侧栏树过滤 + 卡片筛选(搜索词 + 侧栏/欢迎页 chip)。 */
(function () {
  "use strict";
  var W = window.__work, doc = document;
  if (!W || !W.state) return;
  var qa = W.qa, on = W.on, norm = W.norm, sideQ = doc.getElementById("side-q");
  var STATUS = {}, unread = false;
  (Array.isArray(window.__INDEX__) ? window.__INDEX__ : []).forEach(function (e) {
    if (e && e.anchor) STATUS[e.anchor] = e.status || "";
  });
  function unreadOk(it) {   /* 只看未完成:课看打开次数 = 0;笔记看 status != done */
    var key = it.getAttribute("data-key");
    if (it.getAttribute("data-kind") === "course") return parseInt(it.getAttribute("data-count") || "0", 10) === 0;
    return STATUS[key] !== "done";
  }
  function filterTree(term) {   /* 词 + 未完成双条件;整组条目全被滤掉时连组头(li)一起收起 */
    term = norm(term);
    qa(".tree-item").forEach(function (it) {
      it.hidden = (!!term && norm(it.textContent).indexOf(term) < 0) || (unread && !unreadOk(it));
    });
    qa(".tree-group").forEach(function (gh) {
      var ul = gh.nextElementSibling, items = ul ? qa(".tree-item", ul) : [], li = gh.parentElement;
      if (li && items.length) li.hidden = (!!term || unread) && !items.some(function (it) { return !it.hidden; });
    });
  }
  function applyCards(term) {   /* 词 + 两处 chip 叠加;site_js 只算欢迎页 chip 的高亮与计数 */
    term = norm(term);
    var want = {}, shown = 0, cards = qa('.group-body[data-kind="welcome"] article.card');
    qa(".chip").forEach(function (ch) {
      var g = ch.getAttribute("data-group") || "kind", v = ch.getAttribute("data-value") || "";
      if (ch.getAttribute("aria-pressed") === "true" && v) (want[g] = want[g] || []).push(v);
    });
    cards.forEach(function (c) {
      var ok = (!term || norm(c.textContent).indexOf(term) >= 0)
        && (!unread || c.getAttribute("data-status") !== "done");
      for (var g in want) { if (want[g].indexOf(c.getAttribute("data-" + g) || "") < 0) ok = false; }
      c.hidden = !ok;
      if (ok) shown++;
    });
    var active = !!term || unread || Object.keys(want).length > 0;
    var cnt = doc.getElementById("count"), emp = doc.getElementById("empty");
    if (cnt) cnt.textContent = active ? shown + " / " + cards.length + " 条" : "";
    if (emp) emp.hidden = shown !== 0;
  }
  function again() { applyCards(sideQ ? sideQ.value : ""); }
  W.filterTree = filterTree; W.applyCards = applyCards;
  W.onlyUnread = function (v) {   /* 命令面板「只看未完成」:过滤树与卡片,再重算命中数 */
    unread = !!v; filterTree(sideQ ? sideQ.value : ""); applyCards(sideQ ? sideQ.value : "");
  };
  on(doc, "click", function (e) {   /* chip / #clear2:site_js 只绑欢迎页 chip,侧栏 chip 与清空在此补 */
    var t = e.target, ch = t && t.closest ? t.closest(".chip") : null;
    if (ch) {
      if (ch.closest('.group-body[data-kind="welcome"]')) { setTimeout(again, 0); return; }   /* 等 site_js 切完 */
      ch.setAttribute("aria-pressed", ch.getAttribute("aria-pressed") === "true" ? "false" : "true");
      again(); return;
    }
    if (t && t.closest && t.closest("#clear2")) {
      unread = false;
      qa(".side-head .chip").forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
      if (sideQ) { sideQ.value = ""; filterTree(""); }
      setTimeout(again, 0);
    }
  });
  on(sideQ, "input", function () { filterTree(sideQ.value); again(); });
})();
"""
