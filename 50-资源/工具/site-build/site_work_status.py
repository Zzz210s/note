#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台·状态栏段(六段可点 + 计数详情浮层 + 状态数字)。

由 `site_work_js.WORK_JS` 拼在第一段(标签 / 布局记忆)之后、第二段(侧栏 / 分屏)
之前执行。本段把状态栏六段的数字与分派收在一起:

  · `W.status` / `W.count` —— 第一段的 `open/activate/close/boot` 调用(首屏由第二段
    的 `W.boot()` 触发,此时本段已就绪);`W.status` 顺带把「本课 N 次」「课程已读 x/y」
    改成实时值,而不是渲染时的死数字。
  · `W.statusAct` —— 六条动作的唯一分派入口,未知 `data-act` 走空分支(不抛异常);
    分派在**点击时**才解析 `W.setPanel/onlyUnread/setSplit/syncTheme`(它们在第二段
    或第三段发布,晚于本段)。
  · 计数详情用自建 `.st-pop` 浮层(**不用 alert**),点浮层 / 点别处 / Esc 都收起。

零依赖、IIFE、无 eval、无内联事件、无 emoji;契约见 `site_dom.CONTRACT`「工作台页」。
"""

STATUS_JS = r"""
/* 工作台·状态栏段:六段可点 + 「本课 N 次」详情浮层 + 状态数字回填。 */
(function () {
  "use strict";
  var doc = document, W = window.__work;
  if (!W || !W.state) return;
  var S = W.state, qa = W.qa, on = W.on, esc = W.esc;
  var stOpen = doc.querySelector(".st-open"), stCount = doc.querySelector(".st-count"),
      stProgress = doc.querySelector(".st-progress");
  var ACTS = ["welcome", "open", "read", "thecount", "theme", "split"];

  function count(key) {   /* 课首次打开 +1,并回填侧栏树次数(第一段 open() 调用) */
    if (!window.__counts || !window.__counts.inc) return;
    var rec = window.__counts.inc(key);
    if (!rec || typeof rec.count !== "number") return;
    qa('.tree-item[data-key="' + esc(key) + '"]').forEach(function (it) {
      it.setAttribute("data-count", rec.count);
      var c = it.querySelector(".t-count"); if (c) c.textContent = rec.count;
    });
  }
  function status() {   /* 打开数 / 当前课次数 / 课程进度(第一段 open/activate/close/boot 调用) */
    if (stOpen) stOpen.textContent = "打开 " + (S.g[1].length + S.g[2].length);
    var key = S.act[S.focus || 1], m = key && W.meta ? W.meta(key) : null;
    var n = (m && m.kind === "lesson" && window.__counts) ? window.__counts.get(key).count : 0;
    if (stCount) stCount.textContent = "本课 " + n + " 次";
    if (stProgress) {
      var all = qa('.tree-item[data-kind="course"]');
      var read = all.filter(function (it) { return parseInt(it.getAttribute("data-count") || "0", 10) > 0; }).length;
      stProgress.textContent = "课程已读 " + read + "/" + all.length;
    }
  }
  W.status = status; W.count = count;

  var popEl = null;
  function el(tag, cls, txt) { var e = doc.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function ensurePop() {
    if (popEl) return popEl;
    popEl = el("div", "st-pop");
    popEl.id = "st-pop";
    popEl.setAttribute("role", "dialog");
    popEl.setAttribute("aria-label", "计数详情");
    popEl.hidden = true;
    doc.body.appendChild(popEl);
    on(popEl, "click", closePop);   /* 点浮层任意处收起 */
    return popEl;
  }
  function showPop(title, rows) {
    var box = el("div", "st-pop-box"), head = el("div", "st-pop-head");
    head.appendChild(el("b", null, title));
    var x = el("button", "st-pop-x", "关闭");
    x.setAttribute("type", "button"); x.setAttribute("aria-label", "关闭计数详情");
    head.appendChild(x); box.appendChild(head);
    rows.forEach(function (r) {
      var p = el("p", "st-pop-row");
      p.appendChild(el("span", "k", r[0])); p.appendChild(el("span", "v", r[1])); box.appendChild(p);
    });
    var pop = ensurePop();
    pop.textContent = ""; pop.appendChild(box); pop.hidden = false;
  }
  function closePop() { if (popEl && !popEl.hidden) popEl.hidden = true; }
  function countDetail() {   /* 当前课的 次数 / 首次 / 最近;没开课就给一句人话 */
    var key = S.act[S.focus || 1], m = key && W.meta ? W.meta(key) : null;
    if (!key || !m || m.kind !== "lesson") { showPop("本课计数", [["状态", "当前没有打开的课程"]]); return; }
    var rec = (window.__counts && window.__counts.get) ? window.__counts.get(key) : { count: 0, first: "", last: "" };
    showPop(m.name || key, [["打开次数", rec.count + " 次"], ["首次", rec.first || "—"], ["最近", rec.last || "—"]]);
  }

  function statusAct(act) {   /* 六条动作唯一入口;未知值走空分支,不抛异常 */
    var g = S.focus || 1;
    if (ACTS.indexOf(act) < 0) return;   /* 默认分支:未知 data-act 无副作用 */
    if (act === "welcome") {                       /* 清空当前组标签,回到欢迎页空态 */
      S.g[g].slice().forEach(function (k) { if (W.close) W.close(k, g); });
      if (W.empty) W.empty(g);
    } else if (act === "open") {                   /* 打开命令面板:侧栏切到 commands */
      if (W.setPanel) W.setPanel("commands");
    } else if (act === "read") {                   /* 只筛未读的课(site_work_filter 的唯一口径) */
      if (W.onlyUnread) W.onlyUnread(true);
    } else if (act === "thecount") {               /* 弹出当前课的计数详情浮层 */
      countDetail();
    } else if (act === "theme") {                  /* 切换主题:与活动栏同一个开关 */
      var tb = doc.getElementById("act-theme");
      if (tb) tb.click(); else if (W.syncTheme) W.syncTheme();
    } else if (act === "split") {                  /* 切换分栏:与 Ctrl+\ 同一条路径 */
      if (W.setSplit) W.setSplit(!S.split);
    }
  }
  W.statusAct = statusAct;
  on(doc, "click", function (e) {
    var b = e.target && e.target.closest ? e.target.closest("button.st-item[data-act]") : null;
    if (!b) return;
    e.preventDefault();
    statusAct(b.getAttribute("data-act"));
  });
  on(doc, "click", function (e) {   /* 点浮层外任意处收起(点 st-item 由上面那条处理,不在此收) */
    if (!popEl || popEl.hidden) return;
    var t = e.target;
    if (t && t.closest && t.closest(".st-pop,button.st-item")) return;
    closePop();
  });
  on(doc, "keydown", function (e) { if (e.key === "Escape") closePop(); });
})();
"""
