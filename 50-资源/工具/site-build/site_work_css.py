#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台布局样式(内联进 `<style>`)。

VS Code 式外壳:标题栏 / 活动栏(48px)/ 侧栏(260px,可折叠)/ 每组标签栏(35px)/
编辑区(含两组分屏)/ 状态栏(24px)。**默认浅色**,`[data-theme=dark]` 另给一套;课用
`iframe.lesson-frame` 内嵌,始终是浅色的独立文档。

外壳是**固定高度**:`body.work{height:100vh;overflow:hidden}`,滚动只发生在侧栏树与
编辑区内部。视觉 token(间距 / 字号 / 圆角 / 阴影 / 亮暗配色)全部来自 `site_work_tokens.
TOKENS`,由本表拼在最前 —— 由此本文与后续各表**不再出现间距 / 字号的 px 魔数**
(自检 `selftest_tokens.py` 卡死:间距只 5 档、字号只 6 档)。图标统一 16px / 1.5px 描边 /
currentColor。内联顺序:`site_css.CSS` → `PROSE` → **WORK_CSS** → `SIDE_CSS` → `PANEL_CSS`
→ `STATES_CSS`(最后一张表补四态)。DOM 契约唯一真源是 `site_dom.CONTRACT`。零外部资源。
"""
from __future__ import annotations

from site_proj_css import PROJ_CSS
from site_work_resp_css import RESPONSIVE_CSS
from site_work_status_css import STATUS_CSS
from site_work_tokens import TOKENS

WORK_CSS = TOKENS + r"""
/* ===== 外壳:固定高度,滚动只发生在侧栏树与编辑区内部(token 重构时误删,已恢复) ===== */
body.work{display:flex;flex-direction:column;height:100vh;overflow:hidden;margin:0;
  background:var(--w-bg);color:var(--w-t1);font:var(--f-base)/1.75 var(--w-font)}
/* ===== 基础:图标与图标按钮(不依赖站内样式表也能自足) ===== */
body.work .icon{width:var(--icon);height:var(--icon);flex:none;fill:none;stroke:currentColor;/* 活动栏图标按 VS Code 口径单独放大(其余图标仍 --icon:16px)*/
  stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
body.work .act .icon{width:24px;height:24px}
body.work .icon-btn{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;
  min-width:0;min-height:0;padding:0;border:0;border-radius:var(--r-ctl);background:none;
  color:var(--w-t2);cursor:pointer}
body.work .icon-btn:hover{background:var(--w-hover);color:var(--w-t1)}
body.work :focus-visible{outline:2px solid var(--w-focus);outline-offset:1px}
/* a.skip 复用站点 site_css(.skip),这里不重复定义避免两份表打架 */
/* ===== 标题栏(35px) ===== */
.titlebar{flex:none;display:flex;align-items:center;gap:var(--s2);height:var(--w-title);
  padding:0 var(--s2) 0 var(--s3);background:var(--w-side-bg);border-bottom:1px solid var(--w-line)}
.tb-title{min-width:0;color:var(--w-t2);font-size:var(--f-sm);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tb-actions{margin-left:auto;display:flex;gap:var(--s1)}
/* ===== 主体:活动栏(48px)+ 侧栏 + 编辑区 ===== */
.work-body{flex:1;display:flex;min-height:0}
.activity{flex:none;width:var(--w-activity);display:flex;flex-direction:column;align-items:center;
  gap:var(--s1);padding:var(--s2) 0;background:var(--w-side-bg);border-right:1px solid var(--w-line)}
.act{position:relative;display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;
  padding:0;border:0;border-radius:var(--r-ctl);background:none;color:var(--w-t2);cursor:pointer}
.act:hover{background:var(--w-hover);color:var(--w-t1)}
.act[aria-pressed=true]{color:var(--w-t1)}
.act[aria-pressed=true]::before{content:"";position:absolute;left:-2px;top:var(--s2);bottom:var(--s2);
  width:2px;border-radius:2px;background:var(--w-accent)}
.act-spacer{flex:1}
/* ===== 侧栏(260px,可折叠;★ data-open=false 必须 visibility:hidden,否则屏外可 Tab) ===== */
.sidebar{flex:none;display:flex;flex-direction:column;min-height:0;width:var(--w-side);overflow:hidden;
  background:var(--w-side-bg);border-right:1px solid var(--w-line);transition:width .15s ease,visibility .15s}
.sidebar[data-open=false]{width:0;border-right:0;visibility:hidden}
/* ★ 侧栏拖拽分隔条(DOM 由 site_work_split 建于 .sidebar 之后;契约见 site_dom) */
.side-resizer{position:relative;flex:none;width:var(--s1);background:transparent;border:0;
  cursor:col-resize;touch-action:none}
.side-resizer::before{content:"";position:absolute;top:0;bottom:0;left:-2px;right:-2px}
.side-resizer:hover,.side-resizer:focus-visible{background:var(--w-accent)}
.sidebar[data-open=false]+.side-resizer{display:none}
body.work.resizing{cursor:col-resize;user-select:none;-webkit-user-select:none}
body.work.resizing .sidebar{transition:none}   /* 拖拽中禁过渡,宽度跟手 */
/* ★ 轻提示:宽 <1024 按 Ctrl+\ 等被拦下的动作给一句人话(不静默失败) */
.work-toast{position:fixed;left:50%;bottom:calc(var(--w-status) + var(--s4));z-index:220;
  transform:translateX(-50%);padding:var(--s2) var(--s4);border-radius:var(--r-card);
  background:var(--w-t1);color:var(--w-bg);font-size:var(--f-sm);box-shadow:var(--sh-1)}
.work-toast[hidden]{display:none!important}
.side-head{flex:none;padding:var(--s2);border-bottom:1px solid var(--w-line)}
.side-head input{width:100%;height:26px;padding:0 var(--s2);border:1px solid var(--w-line);
  border-radius:var(--r-ctl);background:var(--w-input);color:var(--w-t1);font:inherit}
.side-head input:focus{border-color:var(--w-accent)}
.side-head .filters{display:flex;flex-wrap:wrap;gap:var(--s1);margin:var(--s2) 0 0}
.side-head .chip{min-height:22px;padding:0 var(--s2);border-radius:999px;font-size:var(--f-xs)}
.side-tree{flex:1;overflow:auto;padding:var(--s1) 0 var(--s3)}
.tree,.tree ul{list-style:none;margin:0;padding:0}
.tree-item{display:flex;align-items:center;gap:var(--s1);width:100%;min-height:26px;
  padding:var(--s1) var(--s3);border:0;background:none;color:var(--w-t1);font:inherit;
  font-size:var(--f-md);text-align:left;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tree-item:hover{background:var(--w-hover)}
.tree-item[aria-current=true]{background:var(--w-sel);box-shadow:inset 2px 0 0 var(--w-accent)}
.tree-item .t-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis}
.tree-item .t-count{margin-left:auto;color:var(--w-t2);font-size:var(--f-xs);font-variant-numeric:tabular-nums}
.tree-item .badge{flex:none;padding:0 var(--s1);border-radius:3px;font-size:var(--f-xs)}
.tree-item .tag{flex:none;padding:0 var(--s1);border:1px solid var(--w-line);border-radius:999px;
  color:var(--w-t2);font-size:var(--f-xs)}
.tree-item[data-count="0"] .t-count{opacity:.65}
/* 语义色:课程 / 笔记 / 记录 / 项目,由 token 给(亮暗各一套;与 site_css --c-* 同值) */
body.work .badge[data-type=course]{background:var(--w-c-course-soft);color:var(--w-c-course)}
body.work .badge[data-type=know]{background:var(--w-c-know-soft);color:var(--w-c-know)}
body.work .badge[data-type=project]{background:var(--w-c-project-soft);color:var(--w-c-project)}
body.work .badge[data-type=log]{background:var(--w-c-log-soft);color:var(--w-c-log)}
/* ★ .tree-item 是 display:flex,会盖掉 UA 的 [hidden]{display:none};不写这条过滤就看不到效果 */
.tree-item[hidden]{display:none}
.tree-group{display:flex;align-items:center;gap:var(--s1);width:100%;
  padding:var(--s2) var(--s2) var(--s1);border:0;background:none;color:var(--w-t2);font:inherit;
  font-size:var(--f-xs);letter-spacing:.04em;text-align:left;cursor:pointer}
.tree-group .t-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis}
.tree-group .t-count{margin-left:auto;font-variant-numeric:tabular-nums}
/* ★ 分组折叠:aria-expanded=false 时收起该组的 ul */
.tree-group[aria-expanded=false] + ul{display:none}
/* ===== 编辑区:每组自己的标签栏(35px)+ 两组分屏 ===== */
.editor{flex:1;display:flex;flex-direction:column;min-width:0;min-height:0;background:var(--w-editor)}
.group-tabs{flex:none;display:flex;height:var(--w-tab);overflow-x:auto;overflow-y:hidden;
  background:var(--w-side-bg);border-bottom:1px solid var(--w-line);scrollbar-width:thin}
/* 一个标签 = .tab-cell 包住「标签按钮 + 关闭按钮」:button 不能嵌 button */
.tab-cell{flex:none;display:inline-flex;align-items:center;border-right:1px solid var(--w-line)}
.tab{position:relative;display:inline-flex;align-items:center;gap:var(--s1);height:100%;
  padding:0 var(--s1) 0 var(--s3);border:0;background:none;color:var(--w-t2);font:inherit;
  font-size:var(--f-md);white-space:nowrap;cursor:pointer}
.tab:hover{color:var(--w-t1)}
/* ★ 选中标签:顶部强调线 + 文字用强调色(不靠底色 —— 底色与未选几乎同色) */
.tab[aria-selected=true]{color:var(--w-accent);font-weight:600}
.tab[aria-selected=true]::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--w-accent)}
.tab .t-name{max-width:200px;overflow:hidden;text-overflow:ellipsis}
/* ★ .t-close 是纯图标控件:必须是可聚焦的 <button aria-label="关闭标签">,不是装饰 span */
.t-close{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;
  margin:0 var(--s2) 0 var(--s1);padding:0;border:0;border-radius:var(--r-ctl);background:none;
  color:inherit;cursor:pointer}
.t-close:hover{background:var(--w-hover)}
.groups{flex:1;display:grid;grid-template-columns:minmax(0,1fr);min-height:0}
.groups[data-split=true]{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
.group{display:flex;flex-direction:column;min-width:0;min-height:0;border-right:1px solid var(--w-line)}
.group:last-child{border-right:0}
/* 拖拽换组:落点提示 + 拖动中的标签(样式归本表,JS 不再注入 <style>) */
body.work .group.drop-target{outline:2px dashed var(--w-accent);outline-offset:-2px}
body.work .group.drop-target>.group-body{background:var(--w-accent-soft)}
body.work .tab-cell.dragging{opacity:.5}
/* ★ 未分屏时第二组必须隐藏(否则空壳占半屏) */
.groups[data-split=false] .group[data-group="2"]{display:none}
.group-body{flex:1;min-height:0;overflow:auto;background:var(--w-editor)}
.group-body[data-kind=welcome]{padding:0}
.group-body[data-kind=note]{padding:var(--s4) var(--s5)}
.group-body[data-kind=lesson]{display:flex;flex-direction:column;padding:0}
/* 标题条:这是内嵌的独立页面,不是"没做适配" */
.group-body[data-kind=lesson]::before{content:"内嵌文档 · 该课为独立页面,页面样式不随工作台主题切换";
  flex:none;padding:var(--s1) var(--s3);background:var(--w-side-bg);border-bottom:1px solid var(--w-line);
  color:var(--w-t2);font-size:var(--f-sm);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* ★ height:100% 必须写:缺则 iframe 退化成默认 150px,课区一片空白 */
.lesson-frame{flex:1;min-height:0;height:100%;margin:var(--s2);border:1px solid var(--w-line);
  border-radius:var(--r-frame);background:#fff} /* ★ 课恒浅色:内嵌文档不随工作台换肤 */
.note-body{max-width:78ch;margin:0 auto}
/* ★ [hidden] 必须压过 [data-kind=lesson] 的 display:flex(同为 (0,2,0),用 !important 兜底) */
.group-body[hidden]{display:none!important}
/* ===== 状态栏(24px;样式在 site_work_status_css.STATUS_CSS,末尾拼入本表) ===== */
.side-mask{display:none} /* ★ 遮罩由 WORK_CSS 负责(站点 site_css 里也有一份,以本份为准) */
/* ★ 响应式五档断点搬去 site_work_resp_css.RESPONSIVE_CSS(PROJ_CSS 之后拼入),
   基线里不再留媒体查询 */
/* ===== 无障碍:减少动效 ===== */
@media (prefers-reduced-motion:reduce){
  body.work *,body.work *::before,body.work *::after{transition:none!important;animation:none!important}
}
/* ===== 打印:去掉工作台外壳,只留正文 ===== */
@media print{
  .titlebar,.activity,.sidebar,.group-tabs,.statusbar,.side-mask,.t-close,.skip{display:none!important}
  body.work{display:block;height:auto;overflow:visible;padding-bottom:0;background:#fff;color:#000}
  .work-body,.editor,.groups,.groups[data-split=true],.group,.group-body{display:block;min-height:0;
    border:0;overflow:visible}
  .group-body{background:#fff}
  .group-body[hidden]{display:none!important}
  .group-body[data-kind=note]{padding:0}
  .group-body[data-kind=lesson]::before{display:none}
  .lesson-frame{height:70vh;margin:0;border:0;border-radius:0}
}
/* ===== 命令面板 / 快速打开(site_work_palette.PALETTE_JS 建 DOM,样式收在这里) ===== */
.palette{position:fixed;inset:0;z-index:200;display:flex;align-items:flex-start;justify-content:center;background:rgba(0,0,0,.28)}
.palette[hidden]{display:none!important}
.palette-box{margin-top:10vh;width:min(620px,92vw);max-height:72vh;display:flex;flex-direction:column;
  background:var(--w-bg);color:var(--w-t1);border:1px solid var(--w-line);
  border-radius:var(--r-card);box-shadow:0 12px 40px rgba(0,0,0,.28);overflow:hidden}
#palette-q{flex:none;padding:var(--s3) var(--s4);border:0;border-bottom:1px solid var(--w-line);
  background:var(--w-input);color:inherit;font:inherit;outline:none}
#palette-list{margin:0;padding:var(--s1);list-style:none;overflow:auto}
#palette-list li{display:flex;align-items:baseline;gap:var(--s2);padding:var(--s2) var(--s3);
  border-radius:var(--r-ctl);cursor:pointer}
#palette-list li[aria-selected=true]{background:var(--w-accent-soft)}
#palette-list .badge{flex:none;padding:0 var(--s1);border-radius:3px;background:var(--w-hover);font-size:var(--f-xs)}
#palette-list .p-name{font-size:var(--f-base)}
#palette-list .p-proj,#palette-list .p-hint{margin-left:auto;color:var(--w-t2);font-size:var(--f-sm)}
.palette-hint{flex:none;padding:var(--s2) var(--s3);border-top:1px solid var(--w-line);
  color:var(--w-t2);font-size:var(--f-sm)}
"""

WORK_CSS += PROJ_CSS
WORK_CSS += RESPONSIVE_CSS   # 必须晚于 PROJ_CSS:同权重覆写卡片的 --proj-max
WORK_CSS += STATUS_CSS
