#!/usr/bin/env python3
"""0-Note 在线阅读站 · 交互脚本(内联进 <script>)。

`JS` 是 IIFE:零依赖、无 eval、无内联事件属性;DOM 契约与 `site_css.CSS` 顶部一致。
消费渲染层内联的 `window.__INDEX__ = [{title,summary,text,kind,status,anchor,href}, …]`
(`anchor` == 卡片 id);功能:主题记忆 / 输入即筛 + `<mark>` 高亮 + 命中计数 / 类型与状态
筛选 chip(带计数、无结果禁用)/ Ctrl-K 与 Cmd-K、↑↓、Enter 键盘 / IntersectionObserver
目录联动 / 滚动 >600px 返回顶部 / 锚点目标卡 `.hit` 1.5s。依赖 id/class:`#q #count #empty
#clear #clear2 #theme #menu #toTop .search-wrap .chip[data-group][data-value][aria-pressed]
.side .side-mask .toc a .sec .cards .card .card-title a .card-sum`。
"""

JS = r"""
/* 站点交互:主题 / 搜索 / 筛选 / 键盘 / 目录联动 / 返回顶部 / 锚点高亮。 */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  var q = doc.getElementById("q"), wrap = doc.querySelector(".search-wrap");
  var countEl = doc.getElementById("count"), emptyEl = doc.getElementById("empty");
  var cards = Array.prototype.slice.call(doc.querySelectorAll(".cards .card"));
  var chips = Array.prototype.slice.call(doc.querySelectorAll(".chip"));
  function reduce() { return !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches); }
  function smooth() { return reduce() ? "auto" : "smooth"; }
  /* 1. 主题:localStorage 优先,否则跟随系统 */
  var KEY = "note-theme";
  function savedTheme() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function setTheme(t) {
    root.setAttribute("data-theme", t);
    var b = doc.getElementById("theme");
    if (b) { b.setAttribute("aria-pressed", t === "dark" ? "true" : "false"); b.title = t === "dark" ? "切换到亮色主题" : "切换到暗色主题"; }
  }
  var st = savedTheme(), sysDark = !!(window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches);
  setTheme(st === "dark" || st === "light" ? st : (sysDark ? "dark" : "light"));
  var themeBtn = doc.getElementById("theme");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    setTheme(next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
  });
  /* 2. 索引 / 卡片原文 */
  var BY_ID = {};
  (Array.isArray(window.__INDEX__) ? window.__INDEX__ : []).forEach(function (e) { if (e && e.anchor) BY_ID[e.anchor] = e; });
  function textOf(c) {
    var e = BY_ID[c.id];
    return e ? ((e.title || "") + " " + (e.summary || "") + " " + (e.text || "")).toLowerCase() : c.textContent.toLowerCase();
  }
  function fields(c) { return [c.querySelector(".card-title a"), c.querySelector(".card-sum")]; }
  var orig = new Map();
  cards.forEach(function (c) { c.tabIndex = -1; fields(c).forEach(function (el) { if (el) orig.set(el, el.textContent); }); });
  function mark(el, term) {
    var base = orig.get(el);
    if (base == null) return;
    el.textContent = "";
    if (!term) { el.textContent = base; return; }
    var low = base.toLowerCase(), pos = 0, i;
    while ((i = low.indexOf(term, pos)) >= 0) {
      if (i > pos) el.appendChild(doc.createTextNode(base.slice(pos, i)));
      var m = doc.createElement("mark");
      m.textContent = base.slice(i, i + term.length);
      el.appendChild(m);
      pos = i + term.length;
    }
    if (pos < base.length) el.appendChild(doc.createTextNode(base.slice(pos)));
  }
  /* 3. 筛选状态与计数 */
  function picked() {
    var out = {};
    chips.forEach(function (ch) {
      if (ch.getAttribute("aria-pressed") === "true") {
        var g = ch.dataset.group || "kind";
        (out[g] = out[g] || []).push(ch.dataset.value || "");
      }
    });
    return out;
  }
  function valOf(c, g) { return g === "status" ? (c.dataset.status || "") : (c.dataset.kind || ""); }
  function groupsOk(c, want) {
    for (var g in want) { if (want[g].length && want[g].indexOf(valOf(c, g)) < 0) return false; }
    return true;
  }
  function queryOk(c, term) { return !term || textOf(c).indexOf(term) >= 0; }
  function countFor(ch, term, want) {
    var g = ch.dataset.group || "kind", v = ch.dataset.value || "", other = {}, n = 0;
    for (var k in want) { if (k !== g) other[k] = want[k]; }
    cards.forEach(function (c) { if (queryOk(c, term) && groupsOk(c, other) && valOf(c, g) === v) n++; });
    return n;
  }
  /* 4. 应用搜索 + 筛选(输入即筛) */
  function apply() {
    var term = q ? q.value.trim().toLowerCase() : "";
    var want = picked(), shown = 0;
    cards.forEach(function (c) {
      var ok = queryOk(c, term) && groupsOk(c, want);
      c.hidden = !ok;
      if (ok) shown++;
      fields(c).forEach(function (el) { if (el) mark(el, term); });
    });
    chips.forEach(function (ch) {
      var n = countFor(ch, term, want), b = ch.querySelector(".n");
      if (b) b.textContent = n;
      ch.disabled = ch.getAttribute("aria-pressed") !== "true" && n === 0;
    });
    var on = !!term || Object.keys(want).length > 0;
    if (countEl) countEl.textContent = on ? shown + " / " + cards.length + " 条" : "";
    if (wrap) wrap.classList.toggle("has-text", !!term);
    if (emptyEl) emptyEl.hidden = shown !== 0;
  }
  if (q) {
    q.addEventListener("input", apply);
    q.addEventListener("keydown", function (e) { if (e.key === "Escape") { q.value = ""; apply(); q.blur(); } });
  }
  chips.forEach(function (ch) {
    ch.addEventListener("click", function () {
      ch.setAttribute("aria-pressed", ch.getAttribute("aria-pressed") === "true" ? "false" : "true");
      apply();
    });
  });
  var clearBtn = doc.getElementById("clear");
  if (clearBtn) clearBtn.addEventListener("click", function () { if (q) { q.value = ""; apply(); q.focus(); } });
  var clear2 = doc.getElementById("clear2");
  if (clear2) clear2.addEventListener("click", function () {
    if (q) q.value = "";
    chips.forEach(function (ch) { ch.setAttribute("aria-pressed", "false"); });
    apply();
  });
  /* 5. 键盘:Ctrl-K / Cmd-K 聚焦,↑↓ 移动,Enter 打开 */
  function shownCards() { return cards.filter(function (c) { return !c.hidden; }); }
  function focusCard(c) {
    cards.forEach(function (x) { x.classList.toggle("focused", x === c); });
    c.focus({ preventScroll: true });
    c.scrollIntoView({ block: "center", behavior: smooth() });
  }
  function move(dir) {
    var v = shownCards();
    if (!v.length) return;
    var cur = v.indexOf(doc.activeElement && doc.activeElement.closest(".card"));
    var i = cur < 0 ? (dir > 0 ? 0 : v.length - 1) : Math.min(v.length - 1, Math.max(0, cur + dir));
    focusCard(v[i]);
  }
  function openCard(c) {
    var a = c.querySelector(".card-title a"), href = a ? (a.getAttribute("href") || "") : "";
    if (href && href.charAt(0) !== "#") window.open(href, "_blank", "noopener");
    else { location.hash = "#" + c.id; hit(c); }
  }
  doc.addEventListener("keydown", function (e) {
    var ae = doc.activeElement, card = ae && ae.closest ? ae.closest(".card") : null;
    if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) { e.preventDefault(); if (q) { q.focus(); q.select(); } return; }
    if (ae !== q && !card) return;
    if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (e.key === "Enter" && card) { e.preventDefault(); openCard(card); }
  });
  /* 6. 锚点跳转 -> 目标卡 .hit 1.5s */
  function hit(c) {
    if (!c) return;
    c.classList.add("hit");
    setTimeout(function () { c.classList.remove("hit"); }, 1500);
  }
  function hitHash() {
    if (!location.hash) return;
    var c = doc.getElementById(location.hash.slice(1));
    if (c && c.classList.contains("card")) hit(c);
  }
  window.addEventListener("hashchange", hitHash);
  /* 7. 目录滚动联动 */
  var tocLinks = Array.prototype.slice.call(doc.querySelectorAll(".toc a"));
  var secs = Array.prototype.slice.call(doc.querySelectorAll(".sec"));
  function setActive(id) { tocLinks.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + id); }); }
  if (window.IntersectionObserver && secs.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) setActive(en.target.id); });
    }, { rootMargin: "-20% 0px -70% 0px" });
    secs.forEach(function (s) { io.observe(s); });
  }
  tocLinks.forEach(function (a) {
    a.addEventListener("click", function () { setActive((a.getAttribute("href") || "").slice(1)); drawer(false); });
  });
  /* 8. 返回顶部 + 移动端目录抽屉 */
  var topBtn = doc.getElementById("toTop"), mask = doc.querySelector(".side-mask");
  var side = doc.querySelector(".side"), menuBtn = doc.getElementById("menu");
  function drawer(open) {
    if (!side) return;
    side.classList.toggle("open", open);
    if (mask) mask.classList.toggle("show", open);
    if (menuBtn) menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { drawer(!side.classList.contains("open")); });
  if (mask) mask.addEventListener("click", function () { drawer(false); });
  function onScroll() {
    var y = window.pageYOffset || root.scrollTop || 0;
    doc.body.classList.toggle("scrolled", y > 40);
    if (topBtn) topBtn.classList.toggle("show", y > 600);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  if (topBtn) topBtn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: smooth() }); });
  apply(); onScroll(); hitHash();
})();
"""
