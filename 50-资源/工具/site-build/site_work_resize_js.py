#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台交互·第五段(侧栏宽度:拖分隔条 / 双击复位 / ←→ / 记忆)。

本段是**自足 IIFE**:自己建 `.side-resizer` 并插到 `.sidebar` 之后(契约 `site_dom.CONTRACT`),
只通过 `window.__work.on` 挂事件、把宽度写成 `<html>` 的内联 `--w-side` —— 因此不依赖
第二段(侧栏 / 分屏)的任何局部变量,拼在它之后即可跑。

宽度语义(设计 §8):拖拽 200-420px · 双击复位 260 · 分隔条可 Tab 聚焦,←/→ 每次 16px ·
写 `localStorage['note:side']`。**内联 `--w-side` 优先于断点**:没手动设过时不写内联,
于是走 `site_work_resp_css` 的断点默认(≤768 抽屉 / 769-1023 收窄 220 / ≥1440 280),
变窄再变宽不会被断点值覆盖手动值。读到非法值(非数字 / 越界)视为**未设置**,回到断点默认
(桌面 1200 即 260)。零外部资源、无 eval;`SIDE_WIDTH_JS` 是纯函数,自检用 node 直接跑。
"""
from __future__ import annotations

# 纯函数:非法(非数字 / 越界)-> 回退默认 260。自检 selftest_breakpoints 用 node 直接调用。
SIDE_WIDTH_JS = ('function sideWidth(v) { var n = parseInt(v, 10); '
                 'return (isFinite(n) && n >= 200 && n <= 420) ? n : 260; }')

RESIZE_JS = r"""
/* 工作台·第五段:侧栏宽度(拖分隔条 / 双击复位 260 / ←→ 16px / localStorage note:side)。 */
(function () {
  "use strict";
  var W = window.__work, doc = document;
  if (!W || !W.state) return;
  var root = doc.documentElement, bodyEl = doc.body, sidebar = doc.querySelector(".sidebar");
  var KEY = "note:side", MIN = 200, MAX = 420, DEF = 260;
  /*__SIDE_WIDTH__*/
  function rsrEl() {   /* 分隔条由本段建(渲染层不产出;契约见 site_dom) */
    var r = doc.querySelector(".side-resizer");
    if (r) return r;
    r = doc.createElement("div"); r.className = "side-resizer"; r.tabIndex = 0;
    r.setAttribute("role", "separator"); r.setAttribute("aria-orientation", "vertical");
    r.setAttribute("aria-valuemin", String(MIN)); r.setAttribute("aria-valuemax", String(MAX));
    r.setAttribute("aria-label", "拖动调整侧栏宽度,双击复位");
    if (sidebar && sidebar.parentNode) sidebar.parentNode.insertBefore(r, sidebar.nextSibling);
    else bodyEl.appendChild(r);
    return r;
  }
  var rsr = rsrEl(), cur = DEF;
  function sideNow() { return sidebar ? Math.round(sidebar.getBoundingClientRect().width) : cur; }
  function apply(w) {   /* 内联 --w-side 盖过断点默认;同步 aria-valuenow */
    cur = Math.max(MIN, Math.min(MAX, Math.round(w)));
    root.style.setProperty("--w-side", cur + "px");
    rsr.setAttribute("aria-valuenow", String(cur));
    return cur;
  }
  function store() { try { localStorage.setItem(KEY, String(cur)); } catch (e) {} }
  function read() {   /* 非法 / 缺失 -> 0(视为未设置,宽度交给断点默认) */
    var raw = null; try { raw = localStorage.getItem(KEY); } catch (e) {}
    if (raw == null) return 0;
    var w = sideWidth(raw);
    return (String(w) === String(parseInt(raw, 10))) ? w : 0;
  }
  var saved = read();
  var closed = !!(sidebar && sidebar.getAttribute("data-open") === "false");
  if (saved) cur = apply(saved);
  else cur = closed ? DEF : Math.max(MIN, Math.min(MAX, sideNow()));   /* 起始值 = 断点当前实际宽度 */
  rsr.setAttribute("aria-valuenow", String(cur));
  var dragging = false, startX = 0, startW = 0, lastTap = 0, moved = false;
  function resetSide() { apply(DEF); store(); rsr.focus(); }
  function removeResizing() { if (bodyEl) bodyEl.classList.remove("resizing"); }
  W.on(rsr, "pointerdown", function (e) {
    if (e.button != null && e.button !== 0) return;
    if (Date.now() - lastTap < 350) {   /* ★ 双击复位:自己判定(不依赖 dblclick 事件) */
      lastTap = 0; resetSide(); e.preventDefault(); return;
    }
    dragging = true; moved = false; startX = e.clientX; startW = sideNow();
    if (bodyEl) bodyEl.classList.add("resizing");
    if (rsr.setPointerCapture) { try { rsr.setPointerCapture(e.pointerId); } catch (x) {} }
  });
  W.on(rsr, "pointermove", function (e) {
    if (!dragging) return;
    moved = true;
    apply(startW + (e.clientX - startX));
    e.preventDefault();
  });
  function stop() {
    if (!dragging) return;
    dragging = false;
    removeResizing();
    if (moved) { store(); lastTap = 0; } else { lastTap = Date.now(); }   /* 单击记时刻,等第二击 */
  }
  W.on(rsr, "pointerup", stop);
  W.on(rsr, "pointercancel", stop);
  W.on(rsr, "keydown", function (e) {   /* 分隔条可 Tab 聚焦,←/→ 每次 16px(基线取 cur,避开过渡中间值) */
    if (e.key === "ArrowLeft") apply(cur - 16);
    else if (e.key === "ArrowRight") apply(cur + 16);
    else if (e.key === "Home") resetSide();
    else return;
    store(); e.preventDefault();
  });
  W.sideWidth = sideWidth;   /* 供自检 / 调试:纯函数,无 DOM 依赖 */
})();
""".replace("/*__SIDE_WIDTH__*/", SIDE_WIDTH_JS)
