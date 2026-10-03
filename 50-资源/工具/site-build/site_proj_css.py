#!/usr/bin/env python3
"""0-Note 在线阅读站 · 欢迎页项目卡样式(从 `site_css` 拆出,治其 200 行上限)。

项目卡只在**工作台欢迎页**出现,故放进工作台样式链(`site_work_css.WORK_CSS` 在
`TOKENS` 之后、`STATUS_CSS` 之前拼入本表):色块(项目色)+ 名称 15.5px + 一句话定位
(两行省略)+ 三统计 + 4px 项目色进度条;悬停整卡上浮 1px、边框转强调色、一层极轻阴影。
网格 `auto-fill/minmax(260px,1fr)`,用 `max-width = 4 列宽 + 3 个间距` 把列数封顶在 4。

间距 / 字号一律走 `site_work_tokens` 的 token(`var(--sN)` / `var(--f-*)`);项目配色走四个
语义色 `--w-c-*`(`.proj-card[data-color]` 把项目色映射成 `--pc` / `--pc-soft`,供色块与
进度条共用)。零外部资源、无 @import。
"""

PROJ_CSS = r"""
/* ===== 欢迎页项目卡:色块 + 三统计 + 4px 项目色进度条;网格 auto-fill 封顶 4 列 ===== */
:root{--proj-max:calc(260px*4 + var(--s3)*3)}   /* 4 列宽 + 3 个间距:网格与上方总览/筛选同宽居中对齐 */
.proj-grid{display:grid;gap:var(--s3);margin:0 auto var(--s5);
  grid-template-columns:repeat(auto-fill,minmax(260px,1fr));max-width:var(--proj-max)}
.group-body[data-kind=welcome]>.overview,
.group-body[data-kind=welcome]>.filters,
.group-body[data-kind=welcome]>.search-count{max-width:var(--proj-max);margin-left:auto;margin-right:auto}
.group-body[data-kind=welcome]>.search-count{display:block}
.proj-card{display:flex;flex-direction:column;gap:var(--s2);padding:var(--s4);background:var(--w-side-bg);
  border:1px solid var(--w-line);border-radius:var(--r-card);
  transition:border-color var(--dur-base) var(--ease-out),background var(--dur-base) var(--ease-out)}
.proj-card:hover{border-color:var(--w-accent);background:var(--w-hover)} /* 拾枝 D1/D7:悬停改底色,不用阴影与位移 */
.proj-card[data-color=course]{--pc:var(--w-c-course);--pc-soft:var(--w-c-course-soft)}
.proj-card[data-color=know]{--pc:var(--w-c-know);--pc-soft:var(--w-c-know-soft)}
.proj-card[data-color=log]{--pc:var(--w-c-log);--pc-soft:var(--w-c-log-soft)}
.proj-card[data-color=project]{--pc:var(--w-c-project);--pc-soft:var(--w-c-project-soft)}
.proj-head{display:flex;align-items:center;gap:var(--s2)}
.proj-mark{display:inline-flex;align-items:center;justify-content:center;flex:none;width:var(--s5);height:var(--s5);
  border-radius:var(--r-ctl);background:var(--pc-soft,var(--w-c-project-soft));color:var(--pc,var(--w-c-project));
  font-size:var(--f-md);font-weight:700;line-height:1}
.proj-name{margin:0;font-size:var(--f-card);font-weight:700}
.proj-desc{margin:0;color:var(--w-t2);font-size:var(--f-md);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.proj-foot{margin-top:auto;display:flex;flex-direction:column;gap:var(--s2)}
.proj-stats{display:flex;gap:var(--s3);color:var(--w-t2);font-size:var(--f-sm)}
.proj-stats b{color:var(--w-t1)}
.proj-prog{width:100%;height:4px;-webkit-appearance:none;appearance:none;border:0;
  background:var(--w-hover);border-radius:999px;overflow:hidden}
.proj-prog::-webkit-progress-bar{background:var(--w-hover);border-radius:999px}
.proj-prog::-webkit-progress-value{background:var(--pc,var(--w-accent));border-radius:999px}
.proj-prog::-moz-progress-bar{background:var(--pc,var(--w-accent));border-radius:999px}
"""
