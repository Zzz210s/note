#!/usr/bin/env python3
"""0-Note 在线阅读站 · 侧栏三面板样式(由 `site_render` 内联在 WORK_CSS 之后)。

拆出独立文件只为守住库规「每个 .py ≤ 200 行」——`site_work_css.py` 基线已 199 行,
面板规则塞不进去。内含 `--w-mark` token(命中片段高亮)与资源管理器 / 搜索 / 命令
三个面板的全部规则;契约见 `site_dom.CONTRACT`「工作台页」一段。
"""
from __future__ import annotations

PANEL_CSS = r"""
/* ===== 侧栏三面板:只有与 aside[data-panel] 同值的 .side-body 显示 ===== */
body.work{--w-mark:rgba(255,214,0,.42)}
[data-theme=dark] body.work,body.work[data-theme=dark]{--w-mark:rgba(202,138,4,.40)}
.side-body{flex:1;min-height:0;overflow:auto}
/* ★ .side-body 会盖掉 UA 的 [hidden]{display:none},必须 !important,否则切面板无效果 */
.side-body[hidden]{display:none!important}
.sidebar[data-panel=search] .side-head,.sidebar[data-panel=commands] .side-head{display:none}
.panel-search,.cmds-list{padding:8px}
.panel-search-row{display:flex;gap:6px;margin-bottom:8px}
#panel-q{flex:1;min-width:0;height:30px;padding:0 8px;border:1px solid var(--w-line);border-radius:6px;background:var(--w-input);color:var(--w-t1);font:inherit;font-size:13px}
#panel-q:focus{border-color:var(--w-accent)}
#panel-scope{flex:none;height:30px;border:1px solid var(--w-line);border-radius:6px;background:var(--w-input);color:var(--w-t1);font:inherit;font-size:12px}
.panel-results{list-style:none;margin:0;padding:0}
.panel-results .res{display:flex;flex-direction:column;gap:2px;width:100%;min-height:44px;padding:6px 8px;border:0;border-radius:6px;background:none;color:inherit;text-align:left;font:inherit;font-size:13px;cursor:pointer}
.panel-results .res:hover{background:var(--w-hover)}
.panel-results .res[aria-selected=true]{background:var(--w-accent-soft)}
.panel-results .res-head{display:flex;align-items:center;gap:6px;min-width:0}
.panel-results .res-name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.panel-results .badge{flex:none;padding:0 4px;border-radius:3px;background:var(--w-hover);color:var(--w-t2);font-size:10px}
.panel-results .res-snip{color:var(--w-t2);font-size:12px;line-height:1.45;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.panel-results mark{background:var(--w-mark);color:inherit;border-radius:2px;padding:0 1px}
.panel-empty{display:flex;flex-direction:column;align-items:center;gap:8px;padding:28px 12px;color:var(--w-t2);font-size:12px;text-align:center}
.panel-empty .pe-title{margin:0}
.pe-actions{display:flex;flex-wrap:wrap;gap:6px;justify-content:center}
.pe-btn{min-height:26px;padding:0 10px;border:1px solid var(--w-line);border-radius:999px;background:var(--w-input);color:var(--w-t1);font:inherit;font-size:12px;cursor:pointer}
.pe-btn:hover{background:var(--w-hover);border-color:var(--w-accent)}
.cmds-list{display:flex;flex-direction:column;gap:2px}
.cmd{display:flex;align-items:baseline;gap:8px;width:100%;min-height:32px;padding:6px 8px;border:0;border-radius:6px;background:none;color:var(--w-t1);text-align:left;font:inherit;font-size:13px;cursor:pointer}
.cmd:hover{background:var(--w-hover)}
.cmd-hint{margin-left:auto;color:var(--w-t2);font-size:11px}
.cmd[aria-current=true]{background:var(--w-accent-soft)}
.cmd:disabled{opacity:.45;cursor:not-allowed}
.cmd:focus-visible{outline:1px solid var(--w-accent);outline-offset:-1px}
@media (max-width:768px){
  #panel-q,#panel-scope{height:44px}
  .cmd,.pe-btn{min-height:44px}
}
"""
