#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台布局样式(内联进 <style>)。

VS Code 式外壳:标题栏 / 活动栏(48px)/ 侧栏(260px,可折叠)/ 每组标签栏(35px)/
编辑区(含两组分屏)/ 状态栏(24px)。**默认浅色**(VS Code Light Modern 取向),
`[data-theme=dark]` 另给一套;课用 `iframe.lesson-frame` 内嵌,始终是浅色的独立文档,
靠一条"内嵌文档"标题条说明它未适配工作台,而不是看起来像没做完。

外壳是**固定高度**:`body.work{height:100vh;overflow:hidden}`,滚动只发生在侧栏树与
编辑区内部(长侧栏下 `document.body.scrollHeight == innerHeight`)。正文基线 15px/1.75,
笔记正文复用 `site_css_prose.PROSE` 的 `.card-body` 排版。

DOM 契约的唯一真源是 `site_dom.CONTRACT`(其中「工作台页」一段),site_work_js 与
site_render 照它产出,漏项即坏页面。本模块零外部资源:无 @import、无字体/图标库,
图标全部由渲染层给内联 `<svg class="icon">`,CSS 只定 `.icon` 尺寸。内联顺序:
`site_css.CSS` → `PROSE` → **WORK_CSS(最后,同 specificity 时压过站点基线)**。
"""
from __future__ import annotations

WORK_CSS = r"""
/* ===== token:默认浅色(VS Code Light Modern 取向) ===== */
body.work{
  --w-activity:48px; --w-side:260px; --w-tab:35px; --w-status:24px; --w-title:35px;
  --w-bg:#ffffff; --w-side-bg:#f8f8f8; --w-editor:#ffffff; --w-line:#e5e5e5;
  --w-t1:#1f1f1f; --w-t2:#616161; --w-accent:#005fb8; --w-accent-soft:rgba(0,95,184,.12);
  --w-focus:#005fb8; --w-hover:rgba(0,0,0,.05); --w-input:#ffffff;
  --w-font:var(--font,ui-sans-serif,system-ui,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif);
  /* ★ 固定外壳:高度锁 100vh、滚动只发生在内部;box-sizing 保证 padding-bottom 不撑破视口 */
  box-sizing:border-box;display:flex;flex-direction:column;height:100vh;overflow:hidden;
  margin:0;padding-bottom:var(--w-status);
  background:var(--w-bg);color:var(--w-t1);font:15px/1.75 var(--w-font);-webkit-text-size-adjust:100%;
}
[data-theme=dark] body.work,body.work[data-theme=dark]{
  --w-bg:#1f1f1f; --w-side-bg:#181818; --w-editor:#1f1f1f; --w-line:#2b2b2b;
  --w-t1:#cccccc; --w-t2:#9d9d9d; --w-accent:#0078d4; --w-accent-soft:rgba(0,120,212,.22);
  --w-focus:#4da3ff;   /* ★ 选中树项(accent-soft 底)上焦点环 5.4:1;用 --w-accent 只有 3.13:1 */
  --w-hover:rgba(255,255,255,.07); --w-input:#313131;
}
/* ===== 基础:图标与图标按钮(不依赖站内样式表也能自足) ===== */
body.work .icon{width:16px;height:16px;flex:none;fill:none;stroke:currentColor;stroke-width:1.7;
  stroke-linecap:round;stroke-linejoin:round}
body.work .icon-btn{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;
  min-width:0;min-height:0;padding:0;border:0;border-radius:6px;background:none;color:var(--w-t2);cursor:pointer}
body.work .icon-btn:hover{background:var(--w-hover);color:var(--w-t1)}
body.work :focus-visible{outline:2px solid var(--w-focus);outline-offset:1px}
/* a.skip 的样式复用站点 site_css(.skip),这里不重复定义避免两份表打架 */
/* ===== 标题栏(35px) ===== */
.titlebar{flex:none;display:flex;align-items:center;gap:8px;height:var(--w-title);padding:0 6px 0 12px;
  background:var(--w-side-bg);border-bottom:1px solid var(--w-line)}
.tb-title{min-width:0;color:var(--w-t2);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tb-actions{margin-left:auto;display:flex;gap:2px}
/* ===== 主体:活动栏(48px)+ 侧栏 + 编辑区 ===== */
.work-body{flex:1;display:flex;min-height:0}
.activity{flex:none;width:var(--w-activity);display:flex;flex-direction:column;align-items:center;gap:4px;
  padding:6px 0;background:var(--w-side-bg);border-right:1px solid var(--w-line)}
.act{position:relative;display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;
  padding:0;border:0;border-radius:6px;background:none;color:var(--w-t2);cursor:pointer}
body.work .act .icon{width:22px;height:22px} /* ★ 提权到 (0,3,1):否则被 body.work .icon 压回 16px */
.act:hover{background:var(--w-hover);color:var(--w-t1)}
.act[aria-pressed=true]{color:var(--w-t1)}
.act[aria-pressed=true]::before{content:"";position:absolute;left:-2px;top:8px;bottom:8px;width:2px;
  border-radius:2px;background:var(--w-accent)}
.act-spacer{flex:1}
/* ===== 侧栏(260px,可折叠;★ data-open=false 必须 visibility:hidden,否则屏外可 Tab) ===== */
.sidebar{flex:none;display:flex;flex-direction:column;min-height:0;width:var(--w-side);overflow:hidden;
  background:var(--w-side-bg);border-right:1px solid var(--w-line);transition:width .15s ease,visibility .15s}
.sidebar[data-open=false]{width:0;border-right:0;visibility:hidden}
.side-head{flex:none;padding:8px;border-bottom:1px solid var(--w-line)}
.side-head input{width:100%;height:26px;padding:0 8px;border:1px solid var(--w-line);border-radius:4px;
  background:var(--w-input);color:var(--w-t1);font:inherit}
.side-head input:focus{border-color:var(--w-accent)}
.side-head .filters{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0 0}
.side-head .chip{min-height:22px;padding:0 8px;border-radius:999px;font-size:11px}
.side-tree{flex:1;overflow:auto;padding:4px 0 12px}
.tree,.tree ul{list-style:none;margin:0;padding:0}
.tree-item{display:flex;align-items:center;gap:6px;width:100%;min-height:24px;padding:2px 10px 2px 12px;
  border:0;background:none;color:var(--w-t1);font:inherit;font-size:13px;text-align:left;cursor:pointer;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tree-item:hover{background:var(--w-hover)}
.tree-item[aria-current=true],.tree-item[aria-expanded=true]{background:var(--w-accent-soft)}
.tree-item .t-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis}
.tree-item .t-count{margin-left:auto;color:var(--w-t2);font-size:11px;font-variant-numeric:tabular-nums}
.tree-item .badge{flex:none;padding:0 4px;border-radius:3px;background:var(--w-hover);color:var(--w-t2);font-size:10px}
.tree-item .tag{flex:none;padding:0 5px;border:1px solid var(--w-line);border-radius:999px;color:var(--w-t2);font-size:10px}
.tree-item[data-count="0"] .t-count{opacity:.65}
.tree-group{display:flex;align-items:center;gap:4px;width:100%;padding:6px 10px 2px;border:0;background:none;
  color:var(--w-t2);font:inherit;font-size:11px;letter-spacing:.04em;text-align:left;cursor:pointer}
.tree-group .t-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis}
.tree-group .t-count{margin-left:auto;font-variant-numeric:tabular-nums}
/* ★ 分组折叠:aria-expanded=false 时收起该组的 ul */
.tree-group[aria-expanded=false] + ul{display:none}
/* ===== 编辑区:每组自己的标签栏(35px)+ 两组分屏 ===== */
.editor{flex:1;display:flex;flex-direction:column;min-width:0;min-height:0;background:var(--w-editor)}
/* ★ 只有每组自己的标签栏(VS Code 即如此);外层标签栏已删,不再有 .tabs */
.group-tabs{flex:none;display:flex;height:var(--w-tab);overflow-x:auto;overflow-y:hidden;
  background:var(--w-side-bg);border-bottom:1px solid var(--w-line);scrollbar-width:thin}
/* 一个标签 = .tab-cell 包住「标签按钮 + 关闭按钮」:button 不能嵌 button(HTML 解析器会拆开) */
.tab-cell{flex:none;display:inline-flex;align-items:center;border-right:1px solid var(--w-line)}
.tab{position:relative;display:inline-flex;align-items:center;gap:6px;height:100%;padding:0 4px 0 10px;
  border:0;background:none;color:var(--w-t2);font:inherit;font-size:13px;white-space:nowrap;cursor:pointer}
.tab:hover{color:var(--w-t1)}
/* ★ 选中标签:顶部强调线 + 文字用强调色(不靠底色 —— 底色与未选只差 1.06:1) */
.tab[aria-selected=true]{color:var(--w-accent);font-weight:600}
.tab[aria-selected=true]::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--w-accent)}
.tab .t-name{max-width:200px;overflow:hidden;text-overflow:ellipsis}
/* ★ .t-close 是纯图标控件:必须是可聚焦的 <button aria-label="关闭标签">,不是装饰 span */
.t-close{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;margin:0 6px 0 2px;padding:0;
  border:0;border-radius:4px;background:none;color:inherit;cursor:pointer}
.t-close:hover{background:var(--w-hover)}
.groups{flex:1;display:grid;grid-template-columns:minmax(0,1fr);min-height:0}
.groups[data-split=true]{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
.group{display:flex;flex-direction:column;min-width:0;min-height:0;border-right:1px solid var(--w-line)}
.group:last-child{border-right:0}
/* ★ 未分屏时第二组必须隐藏(否则空壳占半屏) */
.groups[data-split=false] .group[data-group="2"]{display:none}
.group-body{flex:1;min-height:0;overflow:auto;background:var(--w-editor)}
.group-body[data-kind=welcome]{padding:0}
.group-body[data-kind=note]{padding:16px 20px}
.group-body[data-kind=lesson]{display:flex;flex-direction:column;padding:0}
/* 标题条:这是内嵌的独立页面,不是"没做适配" */
.group-body[data-kind=lesson]::before{content:"内嵌文档 · 该课为独立页面,页面样式不随工作台主题切换";
  flex:none;padding:4px 10px;background:var(--w-side-bg);border-bottom:1px solid var(--w-line);
  color:var(--w-t2);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* ★ height:100% 必须写:缺则 iframe 退化成默认 150px,课区一片空白 */
.lesson-frame{flex:1;min-height:0;height:100%;margin:8px;border:1px solid var(--w-line);border-radius:6px;
  background:#fff} /* ★ 课恒浅色:内嵌文档不随工作台换肤 */
.note-body{max-width:78ch;margin:0 auto}
/* ★ [hidden] 必须压过 [data-kind=lesson] 的 display:flex(同为 (0,2,0),用 !important 兜底) */
.group-body[hidden]{display:none!important}
/* ===== 状态栏(24px;★ 固定底部,body 已用 padding-bottom 抵消) ===== */
/* ★ 白字压 --w-accent:浅色 #005fb8 = 6.31:1,暗色 #0078d4 = 4.53:1(≥4.5,12px 小字达标) */
.statusbar{position:fixed;left:0;right:0;bottom:0;z-index:60;display:flex;align-items:center;gap:14px;
  height:var(--w-status);padding:0 10px;background:var(--w-accent);color:#fff;font-size:12px;
  white-space:nowrap;overflow:hidden}
.statusbar span{min-width:0;overflow:hidden;text-overflow:ellipsis}
.st-open{margin-left:auto}
.side-mask{display:none} /* ★ 遮罩由 WORK_CSS 负责(站点 site_css 里也有一份,以本份为准) */
/* ===== 响应式:≤768px 侧栏变抽屉、分屏隐藏、标签横向滚动、状态栏精简 ===== */
@media (max-width:768px){
  /* 45 = 44 内容 + 1px 下边框;站点 site_css 全局 box-sizing:border-box,44 会被边框吃掉 1px */
  body.work{--w-side:min(86vw,300px);--w-tab:45px}
  .activity{border-right:0}
  .sidebar{position:fixed;top:0;bottom:0;left:0;z-index:70;width:min(86vw,300px);overflow:auto;
    transform:translateX(-102%);visibility:hidden;transition:transform .2s ease,visibility .2s}
  .sidebar[data-open=true]{transform:none;visibility:visible}
  .sidebar[data-open=false]{width:min(86vw,300px);border-right:0;visibility:hidden}
  .side-mask.show{display:block;position:fixed;inset:0;z-index:65;background:rgba(0,0,0,.42)}
  .groups[data-split=true]{grid-template-columns:minmax(0,1fr)}
  .groups[data-split=true] .group[data-group="2"]{display:none}
  /* ★ 触达 ≥44px:chip / 图标按钮 / 标签 / 树项 全抬到 44(桌面保持紧凑) */
  .act{width:44px;height:44px}
  .side-head input{height:44px}
  .side-head .chip{min-height:44px;padding:0 14px;font-size:12px}
  body.work .icon-btn{width:44px;height:44px;min-width:44px;min-height:44px}
  .tree-item{min-height:44px}
  .t-close{width:26px;height:26px}
  .st-split,.st-theme{display:none}
  .statusbar{gap:8px;font-size:11px}
  .tb-title{display:none}
  .group-tabs{scrollbar-width:none}
}
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
"""
