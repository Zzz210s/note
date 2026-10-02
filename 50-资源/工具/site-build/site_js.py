#!/usr/bin/env python3
"""0-Note 在线阅读站 · 交互脚本(内联进 <script>)。

DOM/属性契约的唯一真源是 `site_dom.CONTRACT`(渲染层逐字照此产出)。内联索引
`window.__INDEX__` 必须由渲染层按 `json.dumps(index, ensure_ascii=False).replace("<", "\\\\u003c")`
写出:不转义 "<" 时,任一条目含 "</script>" 会提前闭合脚本 → SyntaxError → 整个脚本
不执行(主题/搜索/筛选/目录/返回顶部全死),JSON 尾巴还会当正文显示;"<!--" 无需处理(实测安全)。

`JS` 由两段 IIFE 拼成:本模块的「主题 + 搜索 + 筛选」(小写 haystack 与 NFKC 归一预存,
按键只做 indexOf;全角 ｔｍｕｘ 等同 tmux)与 `site_js_nav.NAV` 的「键盘 / 目录联动 /
返回顶部 / 移动端抽屉 / 锚点 .hit」——两者经同一 DOM 契约协作,拆两段是为守住 200 行上限。
`BOOT` 是首屏主题 IIFE(单行):Task 4 必须把它内联在 `<head>`,消除主题闪烁;
body 尾部仍内联 `JS`,逻辑不变。
"""
from site_js_nav import NAV

_SEARCH = r"""
/* 主题 / 搜索 / 类型与状态筛选:维护卡片 hidden、标题摘要高亮、chip 计数。 */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  var q = doc.getElementById("q"), wrap = doc.querySelector(".search-wrap");
  var countEl = doc.getElementById("count"), emptyEl = doc.getElementById("empty");
  var cards = Array.prototype.slice.call(doc.querySelectorAll(".cards .card"));
  /* 参与「筛选」的 chip 只认欢迎页那一套(侧栏 chip 由 site_work_filter 与 #side-q 叠加,见其 applyCards);
     countChips 含两处 chip,只管 .n 计数与 disabled,不参与 picked()。 */
  var chips = Array.prototype.slice.call(doc.querySelectorAll('.group-body[data-kind="welcome"] .chip'));
  var countChips = Array.prototype.slice.call(doc.querySelectorAll(".chip"));
  /* NFKC 归一 + 小写:全角 ｔｍｕｘ 与 tmux 等价 */
  function norm(s) {
    s = s == null ? "" : String(s);
    return (s.normalize ? s.normalize("NFKC") : s).toLowerCase();
  }
  /* 1. 主题:localStorage 优先,否则跟随系统(BOOT 已在 <head> 抢设一次) */
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
  /* 2. 索引:小写 haystack 初始化时算一次,之后每次按键只做 indexOf */
  var BY_ID = {};
  (Array.isArray(window.__INDEX__) ? window.__INDEX__ : []).forEach(function (e) {
    if (e && e.anchor) { e.low = norm((e.title || "") + " " + (e.summary || "") + " " + (e.text || "")); BY_ID[e.anchor] = e; }
  });
  function textOf(c) { var e = BY_ID[c.id]; return e && e.low != null ? e.low : norm(c.textContent); }
  function queryOk(c, term) { return !term || textOf(c).indexOf(term) >= 0; }
  /* 3. 标题/摘要的原文与归一文本各缓存一份,供 <mark> 用;标记期间不动 DOM 结构以外的东西 */
  function fields(c) { return [c.querySelector(".card-title a"), c.querySelector(".card-sum")]; }
  var orig = new Map(), LOW = new Map();
  cards.forEach(function (c) { c.tabIndex = -1; fields(c).forEach(function (el) { if (el) { orig.set(el, el.textContent); LOW.set(el, norm(el.textContent)); } }); });
  function mark(el, term) {
    var base = orig.get(el);
    if (base == null) return;
    if (!term) { if (el.firstElementChild) el.textContent = base; return; }
    el.textContent = "";
    var low = LOW.get(el) || base, pos = 0, i;
    while ((i = low.indexOf(term, pos)) >= 0) {
      if (i > pos) el.appendChild(doc.createTextNode(base.slice(pos, i)));
      var m = doc.createElement("mark");
      m.textContent = base.slice(i, i + term.length);
      el.appendChild(m);
      pos = i + term.length;
    }
    if (pos < base.length) el.appendChild(doc.createTextNode(base.slice(pos)));
  }
  function restore(el) { if (el && el.firstElementChild) el.textContent = orig.get(el); }
  /* 4. 筛选状态与 chip 计数:空 data-value 视为「无约束」,不会把结果全灭 */
  function picked() {
    var out = {};
    chips.forEach(function (ch) {
      if (ch.getAttribute("aria-pressed") === "true") {
        var g = ch.dataset.group || "kind", v = ch.dataset.value || "";
        if (v) (out[g] = out[g] || []).push(v);
      }
    });
    return out;
  }
  function valOf(c, g) { return g === "status" ? (c.dataset.status || "") : (c.dataset.kind || ""); }
  function groupsOk(c, want) {
    for (var g in want) {
      var w = want[g].filter(function (v) { return v; });
      if (w.length && w.indexOf(valOf(c, g)) < 0) return false;
    }
    return true;
  }
  function countFor(ch, term, want) {
    var g = ch.dataset.group || "kind", v = ch.dataset.value || "", other = {}, n = 0;
    for (var k in want) { if (k !== g) other[k] = want[k]; }
    cards.forEach(function (c) { if (queryOk(c, term) && groupsOk(c, other) && (!v || valOf(c, g) === v)) n++; });
    return n;
  }
  /* 5. 应用搜索 + 筛选(输入即筛;隐藏卡只还原高亮,不重拼) */
  function apply() {
    var term = q ? norm(q.value.trim()) : "";
    var want = picked(), shown = 0;
    cards.forEach(function (c) {
      var ok = queryOk(c, term) && groupsOk(c, want);
      c.hidden = !ok;
      if (ok) { shown++; fields(c).forEach(function (el) { if (el) mark(el, term); }); }
      else fields(c).forEach(restore);
    });
    countChips.forEach(function (ch) {
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
  apply();
})();
"""

JS = _SEARCH + "\n" + NAV

BOOT = (
    '(function(){try{var t=localStorage.getItem("note-theme");'
    'if(t!=="dark"&&t!=="light"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}'
    'document.documentElement.setAttribute("data-theme",t)}catch(e){}})();'
)
