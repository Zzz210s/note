#!/usr/bin/env python3
"""0-Note 在线阅读站 · 样式表(内联进 `<style>`)。

`CSS` 直接内联,零外部资源(无 @import / 字体 CDN / 图标库;图标由渲染层用内联 SVG + `.icon` 定尺寸)。
只覆盖站点组件,不复刻课内样式(`.dfn` 等)。

DOM 契约(渲染层逐字照此产出,site_js 依赖同一套)的唯一真源是 `site_dom.CONTRACT`;本模块把它以
`DOM_CONTRACT` 再导出。视觉标尺定义在 `site_work_tokens`,本表只引用,故不出现间距 / 字号 px 魔数;四态补齐见 `site_work_states`。

对比度(实测,详见 task-6-report.md):正文 `--t1` 亮 15.8 / 暗 17.06 · 次要 `--t2` 亮 6.39 / 暗 6.96 ·
辅助 `--t3` 亮 3.08 / 暗 3.75(仅用于日期 / 计数这类非正文小字)· 强调 `--brand` 亮 5.72 / 暗 7.07。
徽章文字对 `-soft` 底亮色 ≥4.6(6% 淡底)、暗色 ≥5.3(12% 淡底)。
"""
from site_dom import CONTRACT as DOM_CONTRACT

CSS = r"""
/* ===== token:亮色(默认) ===== */
:root{
  --bg:#ffffff; --bg-alt:#f3f4f6; --bg-elv:#ffffff; --bg-mute:#eceef1; --divider:#e1e4e8;
  --t1:#1f2328; --t2:#57606a; --t3:#8b949e;
  --brand:#0b62d0; --brand-2:#8250df; --brand-soft:#f0f6fc;
  --mark:#ffe27a; --mark-fg:#1f2328;
  --c-course:#0b62d0; --c-course-soft:#f0f6fc; --c-know:#1a7f37; --c-know-soft:#f1f7f3;
  --c-project:#8250df; --c-project-soft:#f8f5fd; --c-log:#bc4c00; --c-log-soft:#fbf4f0;
  --c-index:#57606a; --c-index-soft:#eceef1;
  --s-learning:#0b62d0; --s-learning-soft:#f0f6fc; --s-todo:#bc4c00; --s-todo-soft:#fbf4f0;
  --s-done:#1a7f37; --s-done-soft:#f1f7f3; --s-idle:#57606a; --s-idle-soft:#eceef1;
  --bar:56px; --side:296px; --radius:8px;
  --shadow:0 1px 2px rgba(16,24,40,.07);
  --font:ui-sans-serif,system-ui,"Segoe UI","PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"Cascadia Code",Consolas,"Noto Sans Mono CJK SC",monospace;
}
/* ===== token:暗色(slate) ===== */
[data-theme=dark]{
  --bg:#0f172a; --bg-alt:#1e293b; --bg-elv:#1e293b; --bg-mute:#334155; --divider:#334155;
  --t1:#f8fafc; --t2:#94a3b8; --t3:#64748b;
  --brand:#58a6ff; --brand-2:#c4a7ff; --brand-soft:#1b2e4c;
  --mark:#6b5518; --mark-fg:#f8fafc;
  --c-course:#58a6ff; --c-course-soft:#1b2e4c; --c-know:#3fb950; --c-know-soft:#16301f;
  --c-project:#c4a7ff; --c-project-soft:#2a2444; --c-log:#f0883e; --c-log-soft:#3a2c14;
  --c-index:#94a3b8; --c-index-soft:#334155;
  --s-learning:#58a6ff; --s-learning-soft:#1b2e4c; --s-todo:#f0883e; --s-todo-soft:#3a2c14;
  --s-done:#3fb950; --s-done-soft:#16301f; --s-idle:#a9b6c8; --s-idle-soft:#293548;
  --shadow:0 1px 2px rgba(0,0,0,.4);
}
/* ===== 基础 ===== */
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:auto}
body{margin:0;background:var(--bg);color:var(--t1);font-size:var(--f-base);line-height:1.75;
  font-family:var(--font);-webkit-text-size-adjust:100%}
a{color:var(--brand);text-decoration:none} a:hover{text-decoration:underline}
h1,h2,h3{line-height:1.3;margin:0 0 var(--s2)} p{margin:0 0 var(--s2)}
:focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:3px}
code,pre{font-family:var(--mono);font-size:.92em}
mark{background:var(--mark);color:var(--mark-fg);border-radius:2px;padding:0 var(--s1)}
.icon{width:var(--icon);height:var(--icon);flex:none;fill:none;stroke:currentColor;stroke-width:1.5;
  stroke-linecap:round;stroke-linejoin:round}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:var(--s3);top:-60px;z-index:99;background:var(--bg-elv);color:var(--t1);
  padding:var(--s3) var(--s4);border:1px solid var(--divider);border-radius:var(--r-frame)}
.skip:focus{top:var(--s3)}
.muted{color:var(--t3)}
/* ===== 顶栏 ===== */
.bar{position:sticky;top:0;z-index:50;border-bottom:1px solid var(--divider);
  background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px)}
.bar-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:var(--s3);
  min-height:var(--bar);padding:0 var(--s5)}
.brand{font-weight:700;color:var(--t1);white-space:nowrap} .brand small{color:var(--t3);font-weight:400}
.bar .spacer{flex:1} .side-mask{display:none}
.icon-btn{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;padding:0;
  border:1px solid var(--divider);border-radius:var(--r-ctl);background:var(--bg-elv);
  color:var(--t2);cursor:pointer}
.icon-btn:hover{border-color:var(--brand);color:var(--brand)}
.menu-btn{display:none}
.search-wrap{position:relative;display:flex;align-items:center;gap:var(--s2);flex:0 1 320px;min-width:200px}
.search-wrap .search-ico{position:absolute;left:var(--s2);color:var(--t3);pointer-events:none}
.search{flex:1 1 auto;min-width:0;height:40px;padding:0 var(--s3) 0 var(--s5);border:1px solid var(--divider);
  border-radius:var(--r-ctl);background:var(--bg-elv);color:var(--t1);font:inherit}
.search::placeholder{color:var(--t3)} .search:focus{border-color:var(--brand)}
.search:focus-visible{outline:2px solid var(--brand);outline-offset:2px;box-shadow:0 0 0 4px var(--brand-soft)}
.search-wrap.has-text .search{border-color:var(--brand)}
.search-clear{width:30px;height:30px;flex:none;display:none;align-items:center;
  justify-content:center;border:0;border-radius:var(--r-ctl);background:none;color:var(--t3);cursor:pointer}
.search-wrap.has-text .search-clear{display:inline-flex}
.search-clear:hover{color:var(--t1);background:var(--bg-mute)}
.search-count{color:var(--t3);font-size:var(--f-md);white-space:nowrap}
/* ===== 总览 ===== */
.overview{display:flex;flex-wrap:wrap;gap:var(--s1) var(--s5);padding:var(--s4);margin:0 0 var(--s5);
  background:var(--bg-alt);border:1px solid var(--divider);border-radius:var(--r-frame);color:var(--t2);font-size:var(--f-md)}
.overview b{color:var(--t1)}
/* 项目卡样式已拆到 site_proj_css.PROJ_CSS(工作台样式链里拼入,治本表 200 行上限) */
/* ===== 布局:目录 + 内容 ===== */
.layout{max-width:1200px;margin:0 auto;padding:var(--s5) var(--s5) calc(var(--s5)*3)}
.side{font-size:var(--f-md)}
/* 侧栏网格只从 1024px 起生效;769-1023px 保持单列,否则正文列被 296px 侧栏挤到只剩 432px */
@media (min-width:1024px){
  .layout{display:grid;grid-template-columns:var(--side) minmax(0,1fr);gap:var(--s5)}
  .side{position:sticky;top:calc(var(--bar) + var(--s4));align-self:start;max-height:calc(100vh - var(--bar) - var(--s5) - var(--s2));overflow:auto}
}
.toc{margin:0;padding:0;list-style:none}
.toc a{display:flex;align-items:center;gap:var(--s2);padding:var(--s2) var(--s3);border-radius:var(--r-ctl);color:var(--t2)}
.toc a:hover{background:var(--bg-mute);color:var(--t1);text-decoration:none}
.toc a.active{background:var(--brand-soft);color:var(--brand);font-weight:600}
.toc .dot{width:8px;height:8px;flex:none;border-radius:50%;background:var(--s-idle)}
.toc .dot[data-status=learning]{background:var(--s-learning)}.toc .dot[data-status=todo]{background:var(--s-todo)}.toc .dot[data-status=done]{background:var(--s-done)}
.toc .n{margin-left:auto;color:var(--t3);font-size:var(--f-sm);font-variant-numeric:tabular-nums}
.content{min-width:0;max-width:78ch}
.sec{margin:0 0 var(--s5);scroll-margin-top:calc(var(--bar) + var(--s4))}
.sec-title{font-size:var(--f-title);padding-bottom:var(--s2);margin:0 0 var(--s4);border-bottom:1px solid var(--divider)}
.cards{display:grid;gap:var(--s3)}
/* ===== 卡片 ===== */
.card{background:var(--bg-elv);border:1px solid var(--divider);border-radius:var(--r-card);padding:var(--s4);
  scroll-margin-top:calc(var(--bar) + var(--s4));transition:border-color var(--dur-base) var(--ease-out),background var(--dur-base) var(--ease-out)}
.card:hover{border-color:var(--brand);background:var(--w-hover)} /* 拾枝 D7:卡片不用阴影,靠底色 */
.card.focused{outline:2px solid var(--brand);outline-offset:2px}
.card[hidden]{display:none}
.card.hit{border-color:var(--brand);background:var(--brand-soft);box-shadow:0 0 0 3px var(--brand-soft)}
.card-head{display:flex;align-items:baseline;gap:var(--s3);flex-wrap:wrap}
.card-title{margin:0;font-size:var(--f-card)}
.card-title a{color:var(--t1)} .card-title a:hover{color:var(--brand)}
.card-meta{margin-left:auto;display:flex;align-items:center;gap:var(--s1);flex-wrap:wrap}
.card-meta .when{color:var(--t3);font-size:var(--f-sm)}
.card-sum{margin:var(--s2) 0 0;color:var(--t2);font-size:var(--f-base)}
.card-win{margin:var(--s3) 0 0;padding:var(--s2) var(--s3);border-left:3px solid var(--brand);font-size:var(--f-base);background:var(--brand-soft);border-radius:0 var(--r-ctl) var(--r-ctl) 0;color:var(--t2)}
.card-rel{margin:var(--s3) 0 0;display:flex;flex-wrap:wrap;gap:var(--s1);color:var(--t3);font-size:var(--f-sm)}
/* ===== 徽章 ===== */
.badge{display:inline-flex;align-items:center;gap:var(--s1);padding:0 var(--s2);border-radius:999px;
  font-size:var(--f-sm);line-height:1.7;white-space:nowrap;background:var(--bg-mute);color:var(--t2)}
.badge[data-type=course]{background:var(--c-course-soft);color:var(--c-course)}
.badge[data-type=know]{background:var(--c-know-soft);color:var(--c-know)}
.badge[data-type=project]{background:var(--c-project-soft);color:var(--c-project)}
.badge[data-type=log]{background:var(--c-log-soft);color:var(--c-log)}.badge[data-type=index]{background:var(--c-index-soft);color:var(--c-index)}
.badge[data-status=learning]{background:var(--s-learning-soft);color:var(--s-learning)}.badge[data-status=todo]{background:var(--s-todo-soft);color:var(--s-todo)}
.badge[data-status=done]{background:var(--s-done-soft);color:var(--s-done)}.badge[data-status=not-started]{background:var(--s-idle-soft);color:var(--s-idle)}
/* ===== 筛选 chip ===== */
.filters{display:flex;flex-wrap:wrap;align-items:center;gap:var(--s2);margin:0 0 var(--s5)}
.filters .lbl{color:var(--t3);font-size:var(--f-md)}
.chip{display:inline-flex;align-items:center;gap:var(--s1);height:22px;min-height:22px;padding:0 var(--s2);border:1px solid var(--divider);
  border-radius:var(--r-xs);background:var(--bg-elv);color:var(--t2);font:inherit;font-size:var(--f-sm);cursor:pointer}
.chip:hover{border-color:var(--brand);color:var(--t1)}
.chip .n{color:var(--t3);font-size:var(--f-xs);font-variant-numeric:tabular-nums}
.chip[aria-pressed=true]{background:var(--brand-soft);border-color:var(--brand);color:var(--brand);font-weight:600}
.chip[aria-pressed=true] .n{color:inherit}
.chip:disabled{opacity:.45;cursor:not-allowed;border-style:dashed}
/* ===== 空结果 / 返回顶部 / 页脚 ===== */
.no-result{padding:var(--s5);margin:0;text-align:center;color:var(--t2);border:1px dashed var(--divider);
  border-radius:var(--r-frame)}
.link-btn{border:0;background:none;color:var(--brand);font:inherit;cursor:pointer;text-decoration:underline}
.to-top{position:fixed;right:var(--s5);bottom:var(--s5);z-index:40;width:44px;height:44px;display:inline-flex;
  align-items:center;justify-content:center;border:1px solid var(--divider);border-radius:50%;
  background:var(--bg-elv);color:var(--t2);cursor:pointer;box-shadow:var(--shadow);opacity:0;visibility:hidden;
  transform:translateY(6px);transition:opacity .2s ease,transform .2s ease,visibility .2s}
.to-top.show{opacity:1;visibility:visible;transform:none}
.foot{max-width:1200px;margin:0 auto;padding:var(--s5);border-top:1px solid var(--divider);color:var(--t3);font-size:var(--f-md)}
/* ===== 移动端(≤768px) ===== */
@media (max-width:768px){
  .bar-inner{flex-wrap:wrap;gap:var(--s2);min-height:0;padding:var(--s2) var(--s4)}
  .brand{flex:1}
  .search-wrap{order:3;flex:1 1 100%}
  .search{height:44px} .search-clear{width:44px;height:44px}   /* 触达 ≥44px */
  body.scrolled .search-wrap{display:none}          /* 滚动后顶栏收成一行 */
  .menu-btn{display:inline-flex}
  .layout{display:block;padding:var(--s4) var(--s4) calc(var(--s5)*3 + var(--s2))}
  .side{position:fixed;top:0;bottom:0;left:0;width:min(86vw,330px);max-height:none;z-index:70;padding:var(--s4);
    background:var(--bg-elv);border-right:1px solid var(--divider);transform:translateX(-102%);
    visibility:hidden;transition:transform .25s ease,visibility .25s;overflow:auto}
  .side.open{transform:none;visibility:visible}
  .side-mask{position:fixed;inset:0;z-index:65;background:rgba(10,12,16,.45)}
  .side-mask.show{display:block}
  .cards{grid-template-columns:1fr}
  .chip,.icon-btn,.to-top{min-height:44px}
  .chip{padding:0 var(--s4)} .icon-btn{width:44px;height:44px} .toc a,.card-title a{min-height:44px;display:flex;align-items:center}
  .card-meta{margin-left:0;width:100%}
}
/* ===== 无障碍:减少动效 ===== */
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{transition:none !important;animation:none !important}
  html{scroll-behavior:auto}
}
/* ===== 打印:去交互,留正文与目录 ===== */
@media print{
  .bar,.filters,.to-top,.side-mask,.skip,.search-wrap{display:none !important}
  body{background:#fff;color:#000}
  .layout{display:block;max-width:none;padding:0}
  .side{position:static;visibility:visible;max-height:none;overflow:visible;border-bottom:1px solid #bbb;margin-bottom:var(--s3)}
  .card,.proj-card{break-inside:avoid;border-color:#bbb;box-shadow:none;transform:none}
  .card[hidden]{display:block} a{color:#000;text-decoration:none}
  .badge,.overview{border:1px solid #bbb}
}
"""
