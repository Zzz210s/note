#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第三段(侧栏树过滤 + 笔记视图 + 卡片筛选)。

由 `site_work_split.SPLIT_JS` 拼在第二段之后(同一段内联脚本),IIFE 经 `window.__work`
取 `qa/on/norm/state`。本段管三件事:

  · 侧栏区块标题行:整块折叠(`.sec-toggle`)与「只看未读/未完成」(`.sec-filter`);
  · 笔记树视图:按项目(服务端渲染的那棵)`↔` 按标签(从每个笔记项的 `data-tags` 现建,
    不预渲染 → 同一篇笔记不会出现两遍;20 个高频标签分组);
  · 过滤汇总:`#side-q` 搜索词 + 欢迎页 chip + 只看未读,一次性重算侧栏树与条目卡。

`#clear2` 口径 = **清空全部筛选**:欢迎页 chip 由 `site_js` 清,本段清 `#side-q`、
复位「只看未读」与 `.sec-filter`。对外接口 `W.onlyUnread(bool)`(命令面板与状态栏
「课程已读」都用它)与 `W.setNoteView(view?)`(命令面板 note-view;不传则切换)。
拆出本段只为守住库规「每个 .py ≤ 200 行」。零依赖、IIFE、无 eval、无内联事件。
"""

FILTER_JS = r"""
/* 工作台·第三段:侧栏树过滤 + 笔记视图(按项目/按标签)+ 卡片筛选。 */
(function () {
  "use strict";
  var W = window.__work, doc = document;
  if (!W || !W.state) return;
  var qa = W.qa, on = W.on, norm = W.norm, sideQ = doc.getElementById("side-q");
  var STATUS = {}, unread = false, noteView = "project";
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
    var vis = 0;
    qa(".tree-item").forEach(function (it) {
      it.hidden = (!!term && norm(it.textContent).indexOf(term) < 0) || (unread && !unreadOk(it));
      if (!it.hidden) vis++;
    });
    qa(".tree-group").forEach(function (gh) {
      var ul = gh.nextElementSibling, items = ul ? qa(".tree-item", ul) : [], li = gh.parentElement;
      if (li && items.length) li.hidden = (!!term || unread) && !items.some(function (it) { return !it.hidden; });
    });
    var se = doc.getElementById("side-empty");   /* 筛选无命中:显示一句人话 + 清空按钮 */
    if (se) se.hidden = !((!!term || unread) && vis === 0);
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
  function syncUnread() { qa(".sec-filter").forEach(function (b) { b.setAttribute("aria-pressed", unread ? "true" : "false"); }); }
  W.filterTree = filterTree; W.applyCards = applyCards;
  W.onlyUnread = function (v) {   /* 命令面板 / 状态栏「课程已读」:过滤树与卡片,再重算命中数 */
    unread = !!v; syncUnread(); filterTree(sideQ ? sideQ.value : ""); applyCards(sideQ ? sideQ.value : "");
  };
  /* ===== 区块标题行:整块折叠 + 只看未读 ===== */
  qa(".sec-toggle").forEach(function (b) {
    on(b, "click", function () {
      var body = doc.getElementById(b.getAttribute("aria-controls") || "");
      var open = b.getAttribute("aria-expanded") === "false";
      b.setAttribute("aria-expanded", open ? "true" : "false");
      if (body) body.hidden = !open;
    });
  });
  qa(".sec-filter").forEach(function (b) { on(b, "click", function () { W.onlyUnread(!unread); }); });
  /* ===== 笔记视图:按项目(服务端树)/ 按标签(从 data-tags 现建) ===== */
  var noteTree = doc.querySelector('.tree[data-group="note"]'), views = qa(".view-btn[data-view]");
  var projectNodes = noteTree ? Array.prototype.slice.call(noteTree.children) : [];
  function buildTagNodes() {   /* 标签视图:每个标签一个分组,取前 20 个高频标签 */
    var byTag = {}, out = [];
    projectNodes.forEach(function (li) {
      qa(".tree-item[data-tags]", li).forEach(function (it) {
        (it.getAttribute("data-tags") || "").split("|").forEach(function (t) { if (t) (byTag[t] = byTag[t] || []).push(it); });
      });
    });
    Object.keys(byTag).sort(function (a, b) {
      return byTag[b].length - byTag[a].length || (a < b ? -1 : a > b ? 1 : 0);
    }).slice(0, 20).forEach(function (t) {
      var li = doc.createElement("li"), gh = doc.createElement("button"), ul = doc.createElement("ul");
      var nm = doc.createElement("span"), ct = doc.createElement("span");
      gh.type = "button"; gh.className = "tree-group"; gh.setAttribute("aria-expanded", "false");
      nm.className = "t-name"; nm.textContent = "标签:" + t;
      ct.className = "t-count"; ct.textContent = String(byTag[t].length);
      gh.appendChild(nm); gh.appendChild(ct); li.appendChild(gh);
      byTag[t].forEach(function (it) { var row = doc.createElement("li"); row.appendChild(it.cloneNode(true)); ul.appendChild(row); });
      li.appendChild(ul); out.push(li);
    });
    return out;
  }
  function setNoteView(v) {   /* 不传 v 则二选一切换;切换后按当前词/未读重跑过滤 */
    if (!noteTree) return;
    if (v !== "project" && v !== "tag") v = noteView === "project" ? "tag" : "project";
    noteView = v;
    while (noteTree.firstChild) noteTree.removeChild(noteTree.firstChild);
    (v === "tag" ? buildTagNodes() : projectNodes).forEach(function (n) { noteTree.appendChild(n); });
    noteTree.setAttribute("data-view", v);
    views.forEach(function (b) { b.setAttribute("aria-selected", b.getAttribute("data-view") === v ? "true" : "false"); });
    filterTree(sideQ ? sideQ.value : "");
  }
  views.forEach(function (b) { on(b, "click", function () { setNoteView(b.getAttribute("data-view")); }); });
  W.setNoteView = setNoteView; W.noteView = function () { return noteView; };
  syncUnread();
  on(doc, "click", function (e) {   /* chip / #clear2:site_js 只绑欢迎页 chip,本段补清空与复位 */
    var t = e.target, ch = t && t.closest ? t.closest(".chip") : null;
    if (ch) {
      if (ch.closest('.group-body[data-kind="welcome"]')) { setTimeout(again, 0); return; }   /* 等 site_js 切完 */
      ch.setAttribute("aria-pressed", ch.getAttribute("aria-pressed") === "true" ? "false" : "true");
      again(); return;
    }
    if (t && t.closest && (t.closest("#clear2") || t.closest("#side-clear"))) {
      unread = false; syncUnread();
      if (sideQ) { sideQ.value = ""; filterTree(""); }
      setTimeout(again, 0);
    }
  });
  on(sideQ, "input", function () { filterTree(sideQ.value); again(); });
})();
"""
