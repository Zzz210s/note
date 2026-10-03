#!/usr/bin/env python3
"""0-Note 在线阅读站 · 状态栏样式(六段可点 + 「本课 N 次」详情浮层)。

由 `site_work_css.WORK_CSS` 拼在末尾(同 specificity 时压过站点基线),渲染层经它内联。
状态栏固定 24px:`body.work` 已用 `padding-bottom:var(--w-status)` 抵消。规则只服务
`site_parts.statusbar()` 产出的 `button.st-item[data-act]` 与 `site_work_status.STATUS_JS`
自建的 `.st-pop`(点击段才有可观测变化,详见 `site_dom.CONTRACT`「工作台页」)。

配色走 token:亮色 `--w-status-bg:#0b62d0` + 白字(5.72:1),暗色 `--w-status-bg:#1e293b`
+ `--w-status-fg:#58a6ff`(5.79:1),两套都 ≥4.5。间距 / 字号一律用 `var(--sN)` /
`var(--f-*)`(自检卡死 px 魔数)。零外部资源:无 @import、无字体/图标库。
"""
from __future__ import annotations

STATUS_CSS = r"""
/* ===== 状态栏(24px;★ 固定底部,body 已用 padding-bottom 抵消) ===== */
/* ★ 配色成对:亮 白字/蓝底 5.72:1;暗 #58a6ff/#1e293b 5.79:1 —— 11.5px 小字均达标 */
.statusbar{position:fixed;left:0;right:0;bottom:0;z-index:60;display:flex;align-items:center;gap:var(--s3);
  height:var(--w-status);padding:0 var(--s2);background:var(--w-status-bg);color:var(--w-status-fg);
  font-size:var(--f-xs);white-space:nowrap;overflow:hidden}
/* ★ 六段都是 button:高度锁 24px(不抬高状态栏),悬停/按下/焦点三态齐全(禁用见 STATES_CSS) */
.statusbar .st-item{display:block;height:100%;line-height:var(--w-status);min-width:0;padding:0 var(--s1);
  border:0;border-radius:var(--r-ctl);background:none;color:inherit;font:inherit;cursor:pointer;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.statusbar .st-item:hover{background:rgba(255,255,255,.18)}
.statusbar .st-item:active{background:rgba(255,255,255,.32)}
.statusbar .st-item:focus-visible{outline:2px solid #fff;outline-offset:-2px}
.st-open{margin-left:auto}
/* ===== 计数详情浮层(状态栏「本课 N 次」弹出;不许用 alert) ===== */
.st-pop{position:fixed;left:var(--s3);bottom:calc(var(--w-status) + var(--s2));z-index:210;
  background:var(--w-bg);color:var(--w-t1);border:1px solid var(--w-line);border-radius:var(--r-card);
  box-shadow:0 8px 28px rgba(0,0,0,.22);font-size:var(--f-md);min-width:210px;overflow:hidden}
.st-pop[hidden]{display:none!important}
.st-pop-head{display:flex;align-items:center;gap:var(--s2);padding:var(--s2) var(--s3);border-bottom:1px solid var(--w-line)}
.st-pop-x{margin-left:auto;padding:0 var(--s2);height:22px;border:0;border-radius:var(--r-ctl);background:none;
  color:var(--w-t2);font:inherit;font-size:var(--f-sm);cursor:pointer}
.st-pop-x:hover{background:var(--w-hover);color:var(--w-t1)}
.st-pop-row{display:flex;justify-content:space-between;gap:var(--s4);margin:0;padding:var(--s1) var(--s3)}
.st-pop-row .k{color:var(--w-t2)}
/* ===== 窄窗口:状态栏精简为 3 段(条目数 / 打开 / 课程进度) =====
   断点与 site_work_css 一致;此处必须晚于 .st-item 且提权到 (0,2,0),否则被 display:block 压回 */
@media (max-width:768px){
  .statusbar .st-count,.statusbar .st-theme,.statusbar .st-split{display:none}
  /* 触达 ≥44px:只拉宽(min-width),高度仍锁 24,不抬高状态栏 */
  .statusbar .st-item{min-width:44px;padding:0 var(--s2)}
}
"""
