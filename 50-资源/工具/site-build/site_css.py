#!/usr/bin/env python3
"""0-Note 在线阅读站 · 样式表(内联进 <style>)。

`CSS` 直接内联,零外部资源(无 @import / 字体 CDN / 图标库;图标由渲染层用内联 SVG + `.icon` 定尺寸)。
只覆盖站点组件,不复刻课内样式(`.dfn` 等)。

DOM 契约(渲染层逐字照此产出,site_js 依赖同一套)的唯一真源是 `site_dom.CONTRACT`;本模块把它以
`DOM_CONTRACT` 再导出,Task 4 直接读那份。契约覆盖 a.skip / .sr / .search-ico / .search-clear / .spacer /
.menu-btn / .link-btn / .when / .lbl、五个图标控件的无障碍名与 aria 属性、`.content` 子节点归属、
内联索引 JSON 的转义规则(漏项即坏页面,契约里标 ★)。
徽章 data-type:course/know/project/log/index/template;data-status 同上状态色。
正文对比度(15px ≥4.5):亮 t1 15.8 / t2 7.87 / t3 4.83 / brand 5.82;暗 t1 14.9 / t2 9.79 / t3 5.94 / brand 7.53。
"""
from site_dom import CONTRACT as DOM_CONTRACT

CSS = r"""
/* ===== token:亮色(默认) ===== */
:root{
  --bg:#fff; --bg-alt:#f5f6f8; --bg-elv:#fff; --bg-mute:#eef0f3; --divider:#e3e6ea;
  --t1:#1f2328; --t2:#4a5260; --t3:#6b7280;
  --brand:#1f5fd0; --brand-2:#6b46c1; --brand-soft:#e9f0ff;
  --mark:#ffe27a; --mark-fg:#1f2328;
  --c-course:#1a5fc4; --c-course-soft:#e5eeff; --c-know:#14724a; --c-know-soft:#dcf3e7;
  --c-project:#6b3fc4; --c-project-soft:#ece4ff; --c-log:#925b12; --c-log-soft:#fbeed7;
  --c-index:#4d5560; --c-index-soft:#ebeef1;
  --s-learning:#1a5fc4; --s-learning-soft:#e5eeff; --s-todo:#925b12; --s-todo-soft:#fbeed7;
  --s-done:#14724a; --s-done-soft:#dcf3e7; --s-idle:#4d5560; --s-idle-soft:#ebeef1;
  --bar:56px; --side:296px; --radius:8px;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 6px 18px rgba(16,24,40,.07);
  --font:ui-sans-serif,system-ui,"Segoe UI","PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"Cascadia Code",Consolas,"Noto Sans Mono CJK SC",monospace;
}
/* ===== token:暗色 ===== */
[data-theme=dark]{
  --bg:#14171c; --bg-alt:#1a1e24; --bg-elv:#1e232b; --bg-mute:#262c35; --divider:#303640;
  --t1:#e7eaef; --t2:#b8c0cc; --t3:#8b95a5;
  --brand:#7aa7ff; --brand-2:#b39dff; --brand-soft:#1c2b45;
  --mark:#6b5518; --mark-fg:#f2f4f8;
  --c-course:#9cc2ff; --c-course-soft:#1c2b45; --c-know:#7fd6a9; --c-know-soft:#13301f;
  --c-project:#c3aaff; --c-project-soft:#271f42; --c-log:#ffc884; --c-log-soft:#3a2c14;
  --c-index:#aab3c0; --c-index-soft:#262b33;
  --s-learning:#9cc2ff; --s-learning-soft:#1c2b45; --s-todo:#ffc884; --s-todo-soft:#3a2c14;
  --s-done:#7fd6a9; --s-done-soft:#13301f; --s-idle:#aab3c0; --s-idle-soft:#262b33;
  --shadow:0 1px 2px rgba(0,0,0,.5),0 6px 18px rgba(0,0,0,.35);
}
/* ===== 基础 ===== */
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:auto}
body{margin:0;background:var(--bg);color:var(--t1);font:15px/1.75 var(--font);-webkit-text-size-adjust:100%}
a{color:var(--brand);text-decoration:none} a:hover{text-decoration:underline}
h1,h2,h3{line-height:1.3;margin:0 0 8px} p{margin:0 0 8px}
:focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:3px}
code,pre{font-family:var(--mono);font-size:.92em}
mark{background:var(--mark);color:var(--mark-fg);border-radius:2px;padding:0 1px}
.icon{width:1.15em;height:1.15em;flex:none;fill:none;stroke:currentColor;stroke-width:2;
  stroke-linecap:round;stroke-linejoin:round}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:10px;top:-60px;z-index:99;background:var(--bg-elv);color:var(--t1);
  padding:10px 14px;border:1px solid var(--divider);border-radius:var(--radius)}
.skip:focus{top:10px}
.muted{color:var(--t3)}
/* ===== 顶栏 ===== */
.bar{position:sticky;top:0;z-index:50;background:var(--bg);border-bottom:1px solid var(--divider);
  background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px)}
.bar-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:12px;
  min-height:var(--bar);padding:0 20px}
.brand{font-weight:700;color:var(--t1);white-space:nowrap} .brand small{color:var(--t3);font-weight:400}
.bar .spacer{flex:1} .side-mask{display:none}
.icon-btn{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;padding:0;
  border:1px solid var(--divider);border-radius:var(--radius);background:var(--bg-elv);
  color:var(--t2);cursor:pointer}
.icon-btn:hover{border-color:var(--brand);color:var(--brand)}
.menu-btn{display:none}
.search-wrap{position:relative;display:flex;align-items:center;gap:8px;flex:0 1 320px;min-width:200px}
.search-wrap .search-ico{position:absolute;left:10px;color:var(--t3);pointer-events:none}
.search{flex:1 1 auto;min-width:0;height:40px;padding:0 12px 0 34px;border:1px solid var(--divider);
  border-radius:var(--radius);background:var(--bg-elv);color:var(--t1);font:inherit}
.search::placeholder{color:var(--t3)} .search:focus{border-color:var(--brand)}
.search:focus-visible{outline:2px solid var(--brand);outline-offset:2px;box-shadow:0 0 0 4px var(--brand-soft)}
.search-wrap.has-text .search{border-color:var(--brand)}
.search-clear{width:30px;height:30px;flex:none;display:none;align-items:center;
  justify-content:center;border:0;border-radius:6px;background:none;color:var(--t3);cursor:pointer}
.search-wrap.has-text .search-clear{display:inline-flex}
.search-clear:hover{color:var(--t1);background:var(--bg-mute)}
.search-count{color:var(--t3);font-size:13px;white-space:nowrap}
/* ===== 总览 / 项目卡 ===== */
.overview{display:flex;flex-wrap:wrap;gap:4px 20px;padding:14px 16px;margin:0 0 24px;
  background:var(--bg-alt);border:1px solid var(--divider);border-radius:var(--radius);color:var(--t2);font-size:14px}
.overview b{color:var(--t1)}
.proj-grid{display:grid;gap:14px;margin:0 0 32px;grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
.proj-card{display:flex;flex-direction:column;gap:8px;padding:14px 16px;background:var(--bg-elv);border:1px solid var(--divider);border-radius:var(--radius)}
.proj-card:hover{border-color:var(--brand);box-shadow:var(--shadow)}
.proj-name{margin:0;font-size:15px;font-weight:700}
.proj-desc{margin:0;color:var(--t2);font-size:13px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.proj-stats{display:flex;gap:14px;color:var(--t3);font-size:12px;margin-top:auto}
.proj-stats b{color:var(--t1)}
.proj-prog{width:100%;height:6px;-webkit-appearance:none;appearance:none;border:0;
  background:var(--bg-mute);border-radius:999px;overflow:hidden}
progress::-webkit-progress-bar{background:var(--bg-mute);border-radius:999px}
progress::-webkit-progress-value{background:var(--brand);border-radius:999px}progress::-moz-progress-bar{background:var(--brand);border-radius:999px}
/* ===== 布局:目录 + 内容 ===== */
.layout{max-width:1200px;margin:0 auto;padding:24px 20px 72px}
.side{font-size:14px}
/* 侧栏网格只从 1024px 起生效;769-1023px 保持单列,否则正文列被 296px 侧栏挤到只剩 432px */
@media (min-width:1024px){
  .layout{display:grid;grid-template-columns:var(--side) minmax(0,1fr);gap:32px}
  .side{position:sticky;top:calc(var(--bar) + 16px);align-self:start;max-height:calc(100vh - var(--bar) - 32px);overflow:auto}
}
.toc{margin:0;padding:0;list-style:none}
.toc a{display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:6px;color:var(--t2)}
.toc a:hover{background:var(--bg-mute);color:var(--t1);text-decoration:none}
.toc a.active{background:var(--brand-soft);color:var(--brand);font-weight:600}
.toc .dot{width:8px;height:8px;flex:none;border-radius:50%;background:var(--s-idle)}
.toc .dot[data-status=learning]{background:var(--s-learning)}.toc .dot[data-status=todo]{background:var(--s-todo)}.toc .dot[data-status=done]{background:var(--s-done)}
.toc .n{margin-left:auto;color:var(--t3);font-size:12px;font-variant-numeric:tabular-nums}
.content{min-width:0;max-width:78ch}
.sec{margin:0 0 32px;scroll-margin-top:calc(var(--bar) + 14px)}
.sec-title{font-size:20px;padding-bottom:8px;margin:0 0 16px;border-bottom:1px solid var(--divider)}
.cards{display:grid;gap:12px}
/* ===== 卡片 ===== */
.card{background:var(--bg-elv);border:1px solid var(--divider);border-radius:var(--radius);padding:14px 16px;
  scroll-margin-top:calc(var(--bar) + 16px);transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.card:hover{border-color:var(--brand);box-shadow:var(--shadow);transform:translateY(-1px)}
.card.focused{outline:2px solid var(--brand);outline-offset:2px}
.card[hidden]{display:none}
.card.hit{border-color:var(--brand);background:var(--brand-soft);box-shadow:0 0 0 3px var(--brand-soft)}
.card-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.card-title{margin:0;font-size:16px}
.card-title a{color:var(--t1)} .card-title a:hover{color:var(--brand)}
.card-meta{margin-left:auto;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.card-meta .when{color:var(--t3);font-size:12px}
.card-sum{margin:6px 0 0;color:var(--t2);font-size:14px}
.card-win{margin:10px 0 0;padding:8px 12px;border-left:3px solid var(--brand);font-size:14px;background:var(--brand-soft);border-radius:0 6px 6px 0;color:var(--t2)}
.card-rel{margin:10px 0 0;display:flex;flex-wrap:wrap;gap:6px;color:var(--t3);font-size:12px}
/* ===== 徽章 ===== */
.badge{display:inline-flex;align-items:center;gap:4px;padding:1px 8px;border-radius:999px;
  font-size:12px;line-height:1.7;white-space:nowrap;background:var(--bg-mute);color:var(--t2)}
.badge[data-type=course]{background:var(--c-course-soft);color:var(--c-course)}
.badge[data-type=know]{background:var(--c-know-soft);color:var(--c-know)}
.badge[data-type=project]{background:var(--c-project-soft);color:var(--c-project)}
.badge[data-type=log]{background:var(--c-log-soft);color:var(--c-log)}.badge[data-type=index]{background:var(--c-index-soft);color:var(--c-index)}
.badge[data-status=learning]{background:var(--s-learning-soft);color:var(--s-learning)}.badge[data-status=todo]{background:var(--s-todo-soft);color:var(--s-todo)}
.badge[data-status=done]{background:var(--s-done-soft);color:var(--s-done)}.badge[data-status=not-started]{background:var(--s-idle-soft);color:var(--s-idle)}
/* ===== 筛选 chip ===== */
.filters{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 24px}
.filters .lbl{color:var(--t3);font-size:13px}
.chip{display:inline-flex;align-items:center;gap:6px;min-height:32px;padding:0 12px;border:1px solid var(--divider);
  border-radius:999px;background:var(--bg-elv);color:var(--t2);font:inherit;font-size:13px;cursor:pointer}
.chip:hover{border-color:var(--brand);color:var(--t1)}
.chip .n{color:var(--t3);font-size:12px;font-variant-numeric:tabular-nums}
.chip[aria-pressed=true]{background:var(--brand-soft);border-color:var(--brand);color:var(--brand);font-weight:600}
.chip[aria-pressed=true] .n{color:inherit}
.chip:disabled{opacity:.45;cursor:not-allowed;border-style:dashed}
/* ===== 空结果 / 返回顶部 / 页脚 ===== */
.no-result{padding:24px;margin:0;text-align:center;color:var(--t2);border:1px dashed var(--divider);
  border-radius:var(--radius)}
.link-btn{border:0;background:none;color:var(--brand);font:inherit;cursor:pointer;text-decoration:underline}
.to-top{position:fixed;right:20px;bottom:20px;z-index:40;width:44px;height:44px;display:inline-flex;
  align-items:center;justify-content:center;border:1px solid var(--divider);border-radius:50%;
  background:var(--bg-elv);color:var(--t2);cursor:pointer;box-shadow:var(--shadow);opacity:0;visibility:hidden;
  transform:translateY(6px);transition:opacity .2s ease,transform .2s ease,visibility .2s}
.to-top.show{opacity:1;visibility:visible;transform:none}
.foot{max-width:1200px;margin:0 auto;padding:20px;border-top:1px solid var(--divider);color:var(--t3);font-size:13px}
/* ===== 移动端(≤768px) ===== */
@media (max-width:768px){
  .bar-inner{flex-wrap:wrap;gap:8px;min-height:0;padding:8px 14px}
  .brand{flex:1}
  .search-wrap{order:3;flex:1 1 100%}
  .search{height:44px} .search-clear{width:44px;height:44px}   /* 触达 ≥44px */
  body.scrolled .search-wrap{display:none}          /* 滚动后顶栏收成一行 */
  .menu-btn{display:inline-flex}
  .layout{display:block;padding:16px 14px 80px}
  .side{position:fixed;top:0;bottom:0;left:0;width:min(86vw,330px);max-height:none;z-index:70;padding:14px;
    background:var(--bg-elv);border-right:1px solid var(--divider);transform:translateX(-102%);
    visibility:hidden;transition:transform .25s ease,visibility .25s;overflow:auto}
  .side.open{transform:none;visibility:visible}
  .side-mask{position:fixed;inset:0;z-index:65;background:rgba(10,12,16,.45)}
  .side-mask.show{display:block}
  .cards{grid-template-columns:1fr}
  .chip,.icon-btn,.to-top{min-height:44px}
  .chip{padding:0 14px} .icon-btn{width:44px;height:44px} .toc a,.card-title a{min-height:44px;display:flex;align-items:center}
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
  .side{position:static;visibility:visible;max-height:none;overflow:visible;border-bottom:1px solid #bbb;margin-bottom:12px}
  .card,.proj-card{break-inside:avoid;border-color:#bbb;box-shadow:none;transform:none}
  .card[hidden]{display:block} a{color:#000;text-decoration:none}
  .badge,.overview{border:1px solid #bbb}
}
"""
