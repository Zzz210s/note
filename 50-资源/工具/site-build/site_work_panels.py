#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台侧栏三个面板(资源管理器 / 搜索 / 命令)。

把活动栏「搜索」「命令」从「只改 data-panel、侧栏一字未变」做成真面板:
`SEARCH_PANEL_HTML` / `CMDS_PANEL_HTML` 由 `site_render` 插进 `aside.sidebar`,
`PANELS_JS` 内联在 `site_work_js.WORK_JS` 之后(要用 `window.__work`)。契约见
`site_dom.CONTRACT`:三个 `.side-body[data-panel]`,同值才显示;命中片段用
`createTextNode` + `<mark>`,绝不拼进 `innerHTML`。零依赖、IIFE、无 eval、无 emoji。
"""
from __future__ import annotations
from site_work_panels_css import PANEL_CSS

# (data-cmd, 名称, 快捷键/说明);与 PANELS_JS 的 RUN 表按 data-cmd 对齐。
CMDS = [
    ("theme", "切换主题", "浅色 / 深色"), ("welcome", "打开欢迎页", "清空当前组标签"),
    ("side", "收起 / 展开侧栏", "Ctrl+B"),
    ("split", "切换分栏", "Ctrl+\\"),
    ("files", "切到资源管理器", "侧栏面板"), ("search", "切到搜索面板", "Ctrl+K"),
    ("goto", "快速打开条目", "Ctrl+P"), ("palette", "打开命令面板", "Ctrl+Shift+P"),
    ("copy-link", "复制当前条目链接", "当前组打开的条目"),
    ("clear-counts", "清空本地计数", "只清本地增量,烘焙保留"),
    ("scope-all", "搜索范围:全部", "并切到搜索面板"),
    ("scope-course", "搜索范围:课程", "并切到搜索面板"),
]

SEARCH_PANEL_HTML = (
    '<div class="side-body" data-panel="search" hidden><div class="panel-search">'
    '<div class="panel-search-row">'
    '<input id="panel-q" type="search" aria-label="搜索全站" placeholder="搜索全站…" autocomplete="off">'
    '<select id="panel-scope" aria-label="搜索范围">'
    '<option value="all">全部</option><option value="course">课程</option>'
    '<option value="note">笔记</option><option value="tag">标签</option></select></div>'
    '<ul id="panel-results" class="panel-results" role="listbox" aria-label="搜索结果"></ul>'
    '<div id="panel-empty" class="panel-empty"><p class="pe-title">输入关键词开始搜索</p>'
    '<div class="pe-actions">'
    + "".join('<button class="pe-btn" type="button" data-term="%s">%s</button>' % (t, t)
              for t in ("伪终端", "恢复密钥", "tmux"))
    + '</div></div></div></div>'
)

CMDS_PANEL_HTML = (
    '<div class="side-body" data-panel="commands" hidden><div id="cmds-list" class="cmds-list" role="list">'
    + "".join('<button class="cmd" type="button" role="listitem" data-cmd="%s">'
              '<span class="cmd-name">%s</span><span class="cmd-hint">%s</span></button>' % c for c in CMDS)
    + "</div></div>"
)

PANELS_JS = r"""
/* 工作台·面板段:三个侧栏面板的切换 + 搜索(去抖 / 键盘 / 范围 / 命中片段)。 */
(function () {
  "use strict";
  var doc = document, W = window.__work;
  if (!W || !W.state) return;
  var S = W.state, qa = W.qa, on = W.on, IDX = Array.isArray(window.__INDEX__) ? window.__INDEX__ : [];
  var sidebar = doc.querySelector(".sidebar"), qEl = doc.getElementById("panel-q");
  var scopeEl = doc.getElementById("panel-scope"), resEl = doc.getElementById("panel-results");
  var empEl = doc.getElementById("panel-empty"), TAGS = {}, timer = 0, hi = -1;
  var BADGE = { course: "课程", know: "知识", project: "项目" };
  var SCOPE = { course: ["course"], note: ["know", "project"] }, LIMIT = 80, WIDTH = 30;
  function norm(s) { s = s == null ? "" : String(s); return (s.normalize ? s.normalize("NFKC") : s).toLowerCase(); }
  function el(t, c) { var e = doc.createElement(t); if (c) e.className = c; return e; }
  function txt(s) { return doc.createTextNode(s == null ? "" : String(s)); }
  /* 面板切换:aside.sidebar[data-panel] 唯一真源;三个 .side-body 跟着显隐 */
  function syncBodies() {
    var p = sidebar ? sidebar.getAttribute("data-panel") : "files", a = doc.activeElement;
    qa(".side-body[data-panel]").forEach(function (b) { b.hidden = b.getAttribute("data-panel") !== p; });
    if (p === "search" && qEl && (!a || a === doc.body)) { try { qEl.focus(); } catch (e) {} }
  }
  syncBodies();
  if (sidebar && window.MutationObserver) new MutationObserver(syncBodies).observe(sidebar, { attributes: true, attributeFilter: ["data-panel"] });
  qa(".tree-group").forEach(function (g) {   /* 侧栏「标签:」分组 -> 标签名 -> 条目 key */
    var nm = g.querySelector(".t-name"), ul = g.nextElementSibling;
    if (!nm || !ul || nm.textContent.trim().indexOf("标签:") !== 0) return;
    var key = norm(nm.textContent.trim().slice(3));
    qa(".tree-item[data-key]", ul).forEach(function (it) { (TAGS[key] = TAGS[key] || []).push(it.getAttribute("data-key")); });
  });
  function foldMap(text) {   /* 逐字符 NFKC,保留「归一字符 -> 原字符下标」 */
    var out = "", map = [], i, j, n;
    for (i = 0; i < text.length; i++) { n = norm(text.charAt(i)); for (j = 0; j < n.length; j++) { out += n.charAt(j); map.push(i); } }
    return { s: out, map: map };
  }
  function locate(text, q) {
    var i = text.toLowerCase().indexOf(q); if (i >= 0) return { at: i, len: q.length };
    var f = foldMap(text), j = f.s.indexOf(q);
    return j < 0 ? null : { at: f.map[j], len: f.map[Math.min(f.map.length - 1, j + q.length - 1)] - f.map[j] + 1 };
  }
  function snip(text, m) {
    var a = Math.max(0, m.at - WIDTH), b = Math.min(text.length, m.at + m.len + WIDTH);
    return { pre: m.at > WIDTH ? "\u2026" : "", text: text.slice(a, b), hi: m.at - a, len: m.len, post: b < text.length ? "\u2026" : "" };
  }
  function hit(e, q) {
    var t = locate(e.title || "", q); if (t) return { where: 0, at: t.at, snip: snip(e.title, t) };
    var body = (e.summary || "") + " " + (e.text || ""), b = locate(body, q);
    return b ? { where: 1, at: b.at, snip: snip(body, b) } : null;
  }
  function rowEl(e, s) {   /* 结果行:mark 由 DOM 造,索引文本不经 HTML 拼接 */
    var li = el("li", "res"), head = el("span", "res-head"), b = el("span", "badge"), nm = el("span", "res-name");
    li.setAttribute("role", "option"); li.setAttribute("data-key", e.anchor);
    b.setAttribute("data-type", e.kind || "know"); b.textContent = BADGE[e.kind] || "知识";
    nm.textContent = e.title || e.anchor; head.appendChild(b); head.appendChild(nm); li.appendChild(head);
    if (!s) return li;
    var sp = el("span", "res-snip"); sp.appendChild(txt(s.pre)); sp.appendChild(txt(s.text.slice(0, s.hi)));
    if (s.len > 0) { var mk = doc.createElement("mark"); mk.appendChild(txt(s.text.substr(s.hi, s.len))); sp.appendChild(mk); }
    sp.appendChild(txt(s.text.slice(s.hi + s.len) + s.post)); li.appendChild(sp); return li;
  }
  function showEmpty(title, actions) {
    if (!empEl) return;
    resEl.hidden = true; empEl.hidden = false; empEl.querySelector(".pe-title").textContent = title;
    var box = empEl.querySelector(".pe-actions"), i; while (box.firstChild) box.removeChild(box.firstChild);
    for (i = 0; i < actions.length; i++) {
      var btn = el("button", "pe-btn"), a = actions[i]; btn.type = "button"; btn.textContent = a.label;
      if (a.term) btn.setAttribute("data-term", a.term); if (a.act) btn.setAttribute("data-act", a.act);
      box.appendChild(btn);
    }
  }
  function tagKeys(q) { var m = {}, t, i; for (t in TAGS) { if (t.indexOf(q) < 0) continue; for (i = 0; i < TAGS[t].length; i++) m[TAGS[t][i]] = t; } return m; }
  function markSel(rows) { rows.forEach(function (r, i) { r.setAttribute("aria-selected", i === hi ? "true" : "false"); }); }
  function paint() { var rows = qa(".res", resEl); markSel(rows); if (rows[hi] && rows[hi].scrollIntoView) rows[hi].scrollIntoView({ block: "nearest" }); }
  function search() {
    var q = norm(qEl.value).trim(), scope = scopeEl ? scopeEl.value : "all", out = [], i, e, h, keys;
    if (!q) {
      showEmpty("输入关键词开始搜索", [{ label: "伪终端", term: "伪终端" },
        { label: "恢复密钥", term: "恢复密钥" }, { label: "tmux", term: "tmux" }]);
      hi = -1; return;
    }
    keys = scope === "tag" ? tagKeys(q) : null;
    for (i = 0; i < IDX.length && out.length < LIMIT; i++) {
      e = IDX[i];
      if (!e || !e.anchor) continue;
      if (scope === "tag") { if (!(e.anchor in keys)) continue; h = { where: 0, at: 0, snip: { pre: "", text: "标签:" + keys[e.anchor], hi: 0, len: 0, post: "" } }; }
      else { if (scope !== "all" && SCOPE[scope].indexOf(e.kind) < 0) continue; h = hit(e, q); if (!h) continue; }
      out.push({ e: e, h: h });
    }
    out.sort(function (a, b) { return a.h.where - b.h.where || a.h.at - b.h.at; });
    resEl.textContent = ""; for (i = 0; i < out.length; i++) resEl.appendChild(rowEl(out[i].e, out[i].h.snip));
    hi = out.length ? 0 : -1;
    if (!out.length) showEmpty("没有匹配「" + qEl.value.trim() + "」", [{ label: "把范围改成全部", act: "all" }]);
    else { resEl.hidden = false; empEl.hidden = true; paint(); }
  }
  function move(d) {
    var rows = qa(".res", resEl).filter(function (r) { return r.offsetParent !== null; });
    if (!rows.length) return;
    var at = rows.indexOf(resEl.querySelector('.res[aria-selected="true"]'));
    hi = Math.min(rows.length - 1, Math.max(0, (at < 0 ? 0 : at) + d)); markSel(rows);
    rows[hi].scrollIntoView({ block: "nearest" });
  }
  function openRow(alt) {
    var cur = resEl.querySelector('.res[aria-selected="true"]');
    if (!cur) return;
    var g = S.focus || 1, tgt = g === 1 ? 2 : 1, key = cur.getAttribute("data-key");
    if (alt) { if (tgt === 2 && !S.split && W.setSplit) W.setSplit(true); W.open(key, tgt); } else W.open(key, g);
  }
  function fire(key, shift) { doc.dispatchEvent(new KeyboardEvent("keydown", { key: key, ctrlKey: true, shiftKey: !!shift, bubbles: true, cancelable: true })); }
  function copyLink() {
    var key = S.act[S.focus || 1]; if (!key) return;
    var url = location.href.split("#")[0] + "#" + encodeURIComponent(key);
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url)["catch"](function () {});
      else { var ta = doc.createElement("textarea"); ta.value = url; doc.body.appendChild(ta); ta.select(); doc.execCommand("copy"); ta.remove(); }
    } catch (e) {}
  }
  function clearCounts() {
    if (window.__counts && window.__counts.clear) window.__counts.clear();
    qa(".tree-item[data-key]").forEach(function (it) {
      var c = window.__counts && window.__counts.get ? window.__counts.get(it.getAttribute("data-key")).count : 0;
      it.setAttribute("data-count", c); var n = it.querySelector(".t-count"); if (n) n.textContent = c;
    });
  }
  function toSearch(scope) { return function () { W.setPanel("search"); syncBodies(); if (scopeEl) scopeEl.value = scope; search(); }; }
  var RUN = {
    "theme": function () { var b = doc.getElementById("act-theme"); if (b) b.click(); },
    "welcome": function () { W.empty(S.focus || 1); },
    "side": function () { W.setSide(!S.side); }, "split": function () { W.setSplit(!S.split); },
    "files": function () { W.setPanel("files"); }, "search": toSearch("all"),
    "goto": function () { fire("p", false); }, "palette": function () { fire("p", true); },
    "copy-link": copyLink, "clear-counts": clearCounts,
    "scope-all": toSearch("all"), "scope-course": toSearch("course")
  };
  on(qEl, "input", function () { clearTimeout(timer); timer = setTimeout(search, 120); });
  on(scopeEl, "change", search);
  on(qEl, "keydown", function (e) {
    if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (e.key === "Enter") { e.preventDefault(); openRow(e.ctrlKey || e.metaKey); }
    else if (e.key === "Escape") { e.preventDefault(); qEl.value = ""; search(); }
  });
  on(resEl, "click", function (e) { var row = e.target.closest ? e.target.closest(".res") : null; if (row) openRow(e.ctrlKey || e.metaKey); });
  on(empEl, "click", function (e) {
    var b = e.target.closest ? e.target.closest("button") : null;
    if (!b) return;
    if (b.getAttribute("data-term")) { qEl.value = b.getAttribute("data-term"); if (scopeEl) scopeEl.value = "all"; search(); }
    else if (b.getAttribute("data-act") === "all") { if (scopeEl) scopeEl.value = "all"; search(); }
  });
  on(doc.querySelector('.side-body[data-panel="commands"]'), "click", function (e) {
    var b = e.target.closest ? e.target.closest(".cmd") : null;
    if (b && RUN[b.getAttribute("data-cmd")]) RUN[b.getAttribute("data-cmd")]();
  });
  search();   /* 首屏:空状态 + 示例词 */
})();
"""
