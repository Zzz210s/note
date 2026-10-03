#!/usr/bin/env python3
"""0-Note 在线阅读站 · 侧栏两区块样式(内联进 `<style>`,排在 WORK_CSS 之后)。

从 `site_work_css.WORK_CSS` 拆出(该表 197 行,新增即破库规 200 行)。内容:区块标题行
(`.side-sec` / `.sec-head` / `.sec-toggle` / `.sec-filter`)、笔记视图切换(`.view-switch`
/ `.view-btn`)、树行高三档(桌面 26 / 平板 32 / 手机 44)与当前打开项的左侧强调条。

**内联顺序**:CSS → PROSE → WORK_CSS → **SIDE_CSS** → PANEL_CSS。SIDE_CSS 在 WORK_CSS
之后,故它对 `.tree-item` 的 `min-height` / `aria-current` 覆写生效(同权重取后者);
三段行高媒体查询也因此必须整段写在这里,不能只把 1023 那段留在本表、768 那段留在 WORK_CSS。
DOM 契约唯一真源是 `site_dom.CONTRACT`。零外部资源、无 @import。
"""

SIDE_CSS = r"""
/* ===== 侧栏两区块:标题行 + 笔记视图切换 + 行高 26/32/44 ===== */
.side-sec{display:flex;flex-direction:column}
.side-sec + .side-sec{border-top:1px solid var(--w-line)}
.sec-head{display:flex;align-items:center}
.sec-toggle{display:flex;align-items:center;gap:6px;flex:1;min-width:0;min-height:26px;
  padding:2px 6px 2px 10px;border:0;background:none;color:var(--w-t1);
  font:inherit;font-size:13px;font-weight:600;text-align:left;cursor:pointer}
.sec-toggle:hover,.sec-filter:hover{background:var(--w-hover)}
.sec-toggle:focus-visible,.sec-filter:focus-visible,.view-btn:focus-visible{outline:2px solid var(--w-focus);outline-offset:-2px}
.sec-toggle .icon{color:var(--w-t2)}
.sec-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sec-count{color:var(--w-t2);font-size:11px;font-weight:400;font-variant-numeric:tabular-nums}
.sec-caret{flex:none;transition:transform .15s ease}
.sec-toggle[aria-expanded=false] .sec-caret{transform:rotate(-90deg)}
.sec-filter{flex:none;width:22px;height:22px;margin:0 6px 0 2px;padding:0;border:0;border-radius:4px;
  background:none;color:var(--w-t2);cursor:pointer}
.sec-filter[aria-pressed=true]{color:var(--w-accent);background:var(--w-accent-soft)}
.sec-body[hidden]{display:none}
/* 笔记视图切换:按项目 / 按标签 二选一(树项不预渲染,由 site_work_filter 现建) */
.view-switch{display:flex;gap:4px;padding:4px 10px 6px}
.view-btn{flex:1;min-height:22px;padding:0 8px;border:1px solid var(--w-line);border-radius:999px;
  background:none;color:var(--w-t2);font:inherit;font-size:11px;cursor:pointer}
.view-btn[aria-selected=true]{border-color:var(--w-accent);color:var(--w-accent);background:var(--w-accent-soft)}
/* 树行高三档:桌面 26(在 WORK_CSS 基线);平板 32;手机 44(Task 8 若改断点,三档同处一处改) */
@media (max-width:1023px){.tree-item{min-height:32px}.sec-toggle{min-height:32px}}
@media (max-width:768px){.tree-item{min-height:44px}.sec-toggle{min-height:44px}.view-btn{min-height:44px}}
"""
