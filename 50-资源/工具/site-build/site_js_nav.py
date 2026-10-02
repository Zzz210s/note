#!/usr/bin/env python3
"""0-Note 在线阅读站 · 交互脚本·导航段(由 `site_js.JS` 拼进同一段内联脚本)。

`NAV` 是第二个 IIFE:键盘(Ctrl-K / Cmd-K 聚焦搜索、↑↓ 在可见卡间移动、Enter 打开)/
目录滚动联动 + 点击平滑滚到章节 / 滚动 >600px 返回顶部 / 移动端目录抽屉(配 site_css 的
`.side.open` 与 `.side-mask.show`)/ 锚点目标卡 `.hit` 1.5s。

它与 `site_js` 的搜索段经 DOM 协作:只读 `c.hidden`(搜索段写),不重复算筛选;
依赖 `#q #toTop #menu`、`.side`、`.side-mask`、`.toc a`、`.sec`、`.cards .card`、
`html[data-theme]`。DOM/属性契约见 `site_dom.CONTRACT`;两段分开是为守住 200 行上限。
"""

NAV = r"""
/* 导航:键盘 / 目录联动 / 返回顶部 / 移动端抽屉 / 锚点高亮。 */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  var q = doc.getElementById("q");
  var cards = Array.prototype.slice.call(doc.querySelectorAll(".cards .card"));
  function reduce() { return !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches); }
  function smooth() { return reduce() ? "auto" : "smooth"; }
  var topBtn = doc.getElementById("toTop"), mask = doc.querySelector(".side-mask");
  var side = doc.querySelector(".side"), menuBtn = doc.getElementById("menu");
  /* 移动端目录抽屉(关闭态靠 .side 的 visibility:hidden 退出 Tab 序) */
  function drawer(open) {
    if (!side) return;
    side.classList.toggle("open", open);
    if (mask) mask.classList.toggle("show", open);
    if (menuBtn) menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { drawer(!side.classList.contains("open")); });
  if (mask) mask.addEventListener("click", function () { drawer(false); });
  /* 1. 键盘:↑↓ 只在搜索框或卡片聚焦时接管,避免纯阅读时抢方向键 */
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
  function hit(c) {
    if (!c) return;
    c.classList.add("hit");
    setTimeout(function () { c.classList.remove("hit"); }, 1500);
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
  /* 2. 锚点跳转 -> 目标卡 .hit 1.5s(html scroll-behavior 保持 auto,带 hash 打开即瞬时到位,
        否则 2.8MB 页动画滚 1.5s 会拖到 .hit 过期) */
  function hitHash() {
    if (!location.hash) return;
    var c = doc.getElementById(location.hash.slice(1));
    if (c && c.classList.contains("card")) hit(c);
  }
  window.addEventListener("hashchange", hitHash);
  /* 3. 目录滚动联动 + 点击平滑滚到章节 */
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
    a.addEventListener("click", function (e) {
      var id = (a.getAttribute("href") || "").slice(1), t = doc.getElementById(id);
      if (t) { e.preventDefault(); t.scrollIntoView({ block: "start", behavior: smooth() }); }
      setActive(id);
      drawer(false);
    });
  });
  /* 4. 返回顶部 + 移动端顶栏收起 */
  function onScroll() {
    var y = window.pageYOffset || root.scrollTop || 0;
    doc.body.classList.toggle("scrolled", y > 40);
    if (topBtn) topBtn.classList.toggle("show", y > 600);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  if (topBtn) topBtn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: smooth() }); });
  onScroll(); hitHash();
})();
"""
