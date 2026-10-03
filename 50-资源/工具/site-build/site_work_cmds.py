#!/usr/bin/env python3
"""0-Note 在线阅读站 · 侧栏命令面板(命令表 / HTML / 执行分派 + 键盘)。

从 `site_work_panels.py` 拆出:该文件基线已 200 行,而命令面板本轮要补齐到 17 条
(16 条可执行 + 1 条禁用占位),再加键盘导航。命令表 `CMDS` 是唯一真源,HTML 由它
渲染;`CMDS_JS` 里 `RUN` 的键必须与「启用」的命令 id 集合**完全相等**(自检用例
`selftest_panels_js` 逐条实跑,`selftest_panels` 校验键集合),任何一条点了不改变
状态都会被拦下。

执行一律走 `window.__work` 已有接口(empty/setSide/setSplit/setPanel/onlyUnread/
searchScope),不另写标签或分屏逻辑;命令面板与搜索面板的搜索接口由
`site_work_panels.PANELS_JS` 发布(`W.searchScope`)。零依赖、IIFE、无 eval、无内联
事件、无 emoji;契约见 `site_dom.CONTRACT`「工作台页」。
"""
from __future__ import annotations

# (data-cmd, 名称, 快捷键/说明, disabled);RUN 表只覆盖 disabled=0 的那些
CMDS = [
    ("theme", "切换主题", "浅色 / 深色", 0),
    ("welcome", "打开欢迎页", "清空当前组标签", 0),
    ("side", "收起 / 展开侧栏", "Ctrl+B", 0),
    ("split", "切换分栏", "Ctrl+\\", 0),
    ("files", "切到资源管理器", "侧栏面板", 0),
    ("search", "切到搜索面板", "Ctrl+K", 0),
    ("goto", "快速打开条目", "Ctrl+P", 0),
    ("palette", "打开命令面板", "Ctrl+Shift+P", 0),
    ("copy-link", "复制当前条目链接", "当前组打开的条目", 0),
    ("clear-counts", "清空本地计数", "只清本地增量,烘焙保留", 0),
    ("collapse-all", "折叠全部", "收起所有分组", 0),
    ("expand-all", "展开全部", "展开所有分组", 0),
    ("only-unread", "只看未完成", "未读的课 + 未完成笔记", 0),
    ("clear-filters", "清空筛选", "搜索词 / chip / 侧栏筛选", 0),
    ("note-view", "笔记视图:按项目 / 按标签", "Task 5 完成后启用", 1),
    ("scope-all", "搜索范围:全部", "并切到搜索面板", 0),
    ("scope-course", "搜索范围:课程", "并切到搜索面板", 0),
]

ENABLED = [c[0] for c in CMDS if not c[3]]
DISABLED = [c[0] for c in CMDS if c[3]]


def _cmd_html(c: tuple) -> str:
    cid, label, hint, off = c
    dis = ' disabled aria-disabled="true"' if off else ""
    return ('<button class="cmd" type="button" role="listitem" data-cmd="%s"%s>'
            '<span class="cmd-name">%s</span><span class="cmd-hint">%s</span></button>'
            % (cid, dis, label, hint))


CMDS_PANEL_HTML = (
    '<div class="side-body" data-panel="commands" hidden><div id="cmds-list" class="cmds-list" role="list">'
    + "".join(_cmd_html(c) for c in CMDS) + "</div></div>"
)

CMDS_JS = r"""
/* 工作台·命令段:命令面板执行分派 + 键盘(↑↓ 选择 · Enter 执行 · Esc 关闭还焦点)。 */
(function () {
  "use strict";
  var doc = document, W = window.__work;
  if (!W || !W.state) return;
  var S = W.state, qa = W.qa, on = W.on;
  var list = doc.getElementById("cmds-list"), unread = false;
  function groups() { return qa(".tree-group[aria-expanded]"); }
  function setAll(open) { groups().forEach(function (g) { g.setAttribute("aria-expanded", open ? "true" : "false"); }); }
  function fire(key, shift) {
    doc.dispatchEvent(new KeyboardEvent("keydown", { key: key, ctrlKey: true, shiftKey: !!shift, bubbles: true, cancelable: true }));
  }
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
  function label() {   /* 只看未完成 -> 显示全部:按钮文字反映当前过滤状态 */
    var n = list ? list.querySelector('.cmd[data-cmd="only-unread"] .cmd-name') : null;
    if (n) n.textContent = unread ? "显示全部" : "只看未完成";
  }
  function setUnread(v) { unread = !!v; if (W.onlyUnread) W.onlyUnread(unread); label(); }
  function toSearch(scope) { if (W.searchScope) W.searchScope(scope); }
  var RUN = {
    "theme": function () { var b = doc.getElementById("act-theme"); if (b) b.click(); },
    "welcome": function () {
      var g = S.focus || 1, list = S.g[g].slice();   /* 与浮动面板一致:清空当前组标签再回欢迎页 */
      list.forEach(function (k) { if (W.close) W.close(k, g); });
      if (W.empty) W.empty(g);
    },
    "side": function () { if (W.setSide) W.setSide(!S.side); },
    "split": function () { if (W.setSplit) W.setSplit(!S.split); },
    "files": function () { if (W.setPanel) W.setPanel("files"); },
    "search": function () { toSearch("all"); },
    "goto": function () { fire("p", false); },
    "palette": function () { fire("p", true); },
    "copy-link": copyLink, "clear-counts": clearCounts,
    "collapse-all": function () { setAll(false); }, "expand-all": function () { setAll(true); },
    "only-unread": function () { setUnread(!unread); },
    "clear-filters": function () { var b = doc.getElementById("clear2"); if (b) b.click(); setUnread(false); },
    "scope-all": function () { toSearch("all"); }, "scope-course": function () { toSearch("course"); }
  };
  function run(id) { if (id && RUN[id]) RUN[id](); }
  on(list, "click", function (e) {
    var b = e.target && e.target.closest ? e.target.closest(".cmd") : null;
    if (b && !b.disabled) run(b.getAttribute("data-cmd"));
  });
  function btns() { return list ? qa('.cmd:not([disabled])', list) : []; }
  function move(d) {   /* 在启用命令间移动;aria-current 标当前项,与真实焦点同步 */
    var bs = btns(); if (!bs.length) return;
    var at = bs.indexOf(doc.activeElement), cur = list.querySelector('.cmd[aria-current="true"]');
    if (at < 0) at = cur ? bs.indexOf(cur) : -1;
    var i = Math.min(bs.length - 1, Math.max(0, (at < 0 ? (d > 0 ? -1 : bs.length) : at) + d));
    bs.forEach(function (b, j) { b.setAttribute("aria-current", j === i ? "true" : "false"); });
    try { bs[i].focus(); } catch (x) {}
  }
  on(list, "keydown", function (e) {
    var k = e.key;
    if (k === "ArrowDown") { e.preventDefault(); move(1); }
    else if (k === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (k === "Enter") {
      e.preventDefault();
      var a = doc.activeElement;
      run(a && a.getAttribute ? a.getAttribute("data-cmd") : null);
    } else if (k === "Escape") {   /* 关闭命令面板,焦点回到打开它的活动栏按钮 */
      e.preventDefault();
      if (W.setPanel) W.setPanel("files");
      var op = doc.querySelector ? doc.querySelector('.act[data-panel="commands"]') : null;
      if (op && op.focus) { try { op.focus(); } catch (x) {} }
    }
  });
})();
"""
