#!/usr/bin/env python3
"""0-Note 在线阅读站 · 侧栏三面板样式(由 `site_render` 内联在 WORK_CSS 之后)。

拆出独立文件只为守住库规「每个 .py ≤ 200 行」——`site_work_css.py` 基线已 199 行,
面板规则塞不进去。内含 `--w-mark` token(命中片段高亮)与资源管理器 / 搜索 / 命令
三个面板的全部规则;契约见 `site_dom.CONTRACT`「工作台页」一段。间距 / 字号走
`site_work_tokens` 的 token,四态由 `site_work_states.STATES_CSS` 补齐。
"""
from __future__ import annotations

PANEL_CSS = r"""
/* ===== 侧栏三面板:只有与 aside[data-panel] 同值的 .side-body 显示 ===== */
.side-body{flex:1;min-height:0;overflow:auto}
/* ★ .side-body 会盖掉 UA 的 [hidden]{display:none},必须 !important,否则切面板无效果 */
.side-body[hidden]{display:none!important}
.sidebar[data-panel=search] .side-head,.sidebar[data-panel=commands] .side-head{display:none}
.panel-search,.cmds-list{padding:var(--s2)}
.panel-search-row{display:flex;gap:var(--s1);margin-bottom:var(--s2)}
#panel-q{flex:1;min-width:0;height:30px;padding:0 var(--s2);border:1px solid var(--w-line);border-radius:var(--r-ctl);background:var(--w-input);color:var(--w-t1);font:inherit;font-size:var(--f-md)}
#panel-q:focus{border-color:var(--w-accent)}
#panel-scope{flex:none;height:30px;border:1px solid var(--w-line);border-radius:var(--r-ctl);background:var(--w-input);color:var(--w-t1);font:inherit;font-size:var(--f-sm)}
.panel-results{list-style:none;margin:0;padding:0}
.panel-results .res{display:flex;flex-direction:column;gap:var(--s1);width:100%;min-height:44px;padding:var(--s2);border:0;border-radius:var(--r-ctl);background:none;color:inherit;text-align:left;font:inherit;font-size:var(--f-md);cursor:pointer}
.panel-results .res:hover{background:var(--w-hover)}
.panel-results .res[aria-selected=true]{background:var(--w-accent-soft)}
.panel-results .res-head{display:flex;align-items:center;gap:var(--s1);min-width:0}
.panel-results .res-name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.panel-results .badge{flex:none;padding:0 var(--s1);border-radius:3px;background:var(--w-hover);color:var(--w-t2);font-size:var(--f-xs)}
.panel-results .res-snip{color:var(--w-t2);font-size:var(--f-sm);line-height:1.45;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.panel-results mark{background:var(--w-mark);color:inherit;border-radius:2px;padding:0 var(--s1)}
.panel-empty{display:flex;flex-direction:column;align-items:center;gap:var(--s2);padding:var(--s5) var(--s3);color:var(--w-t2);font-size:var(--f-sm);text-align:center}
.panel-empty .pe-title{margin:0}
.pe-actions{display:flex;flex-wrap:wrap;gap:var(--s1);justify-content:center}
.pe-btn{min-height:32px;padding:0 var(--s3);border:1px solid var(--w-line);border-radius:var(--r-ctl);background:var(--w-input);color:var(--w-t1);font:inherit;font-size:var(--f-sm);cursor:pointer}
.pe-btn:hover{background:var(--w-hover);border-color:var(--w-accent)}
.cmds-list{display:flex;flex-direction:column;gap:var(--s1)}
.cmd{display:flex;align-items:baseline;gap:var(--s2);width:100%;min-height:32px;padding:var(--s2);border:0;border-radius:var(--r-ctl);background:none;color:var(--w-t1);text-align:left;font:inherit;font-size:var(--f-md);cursor:pointer}
.cmd:hover{background:var(--w-hover)}
.cmd-hint{margin-left:auto;color:var(--w-t2);font-size:var(--f-xs)}
.cmd[aria-current=true]{background:var(--w-accent-soft)}
.cmd:disabled{opacity:.45;cursor:not-allowed}
.cmd:focus-visible{outline:2px solid var(--w-focus);outline-offset:-2px}
@media (max-width:768px){
  #panel-q,#panel-scope{height:44px}
  .cmd,.pe-btn{min-height:44px}
}
"""
