#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台响应式五档断点(设计 §8)。

由 `site_work_css.WORK_CSS` 拼在 **`site_proj_css.PROJ_CSS` 之后**、`STATUS_CSS` 之前 ——
本表用 `:root{--proj-*}` 覆写卡片网格的列数与封顶宽度,必须晚于 PROJ_CSS 的同权重规则,
否则被它压掉(等权重看先后)。`STATUS_CSS` 仍留在最后(自检断言它 == WORK_CSS 末尾)。

五档:≤480 手机(卡片 1 列)· 481-768 大手机/小平板(抽屉 + 卡片 2 列)· 769-1023 小笔记本
(侧栏自动收窄 220 · 禁分屏 · 卡片 2-3 列)· 1024-1439 常规(分屏可用 · 卡片 3 列)·
≥1440 大屏(侧栏 280 · 卡片 4 列封顶)。窄窗口的抽屉 / 行高 44 / 状态栏 3 段规则同在本表
(原在 WORK_CSS 基线里),断点数值与 `site_work_status_css` 的 768 一致。尺寸走 token
(`--w-*` / `--sN`),不写新的间距 / 字号 px 魔数(卡片列数用 `--proj-max` 表达,不是间距)。
零外部资源、无 @import。
"""
from __future__ import annotations

RESPONSIVE_CSS = r"""
/* ===== 响应式五档断点(设计 §8):≤480 / 481-768 / 769-1023 / 1024-1439 / ≥1440 ===== */
/* ≤480 手机:抽屉 · 单栏 · 卡片 1 列 · 行高 44 · 状态栏 3 段(后两条见下方 768 段) */
@media (max-width:480px){
  .proj-grid{grid-template-columns:minmax(0,1fr)}
}
/* 481-768 大手机 / 小平板:同上,卡片 2 列 */
@media (min-width:481px) and (max-width:768px){
  .proj-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
}
/* 769-1023 小笔记本:侧栏自动收窄 220(未手动设过时)· 默认单栏(禁分屏)· 卡片 2-3 列 */
@media (min-width:769px) and (max-width:1023px){
  :root{--w-side:220px;--proj-max:calc(260px*3 + var(--s3)*2)}
  .groups[data-split=true]{grid-template-columns:minmax(0,1fr)}
  .groups[data-split=true] .group[data-group="2"]{display:none}
}
/* 1024-1439 常规:分屏可用 · 卡片 3 列(网格与总览/筛选同宽,封顶同步) */
@media (min-width:1024px) and (max-width:1439px){
  :root{--proj-max:calc(260px*3 + var(--s3)*2)}
  .proj-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
}
/* ≥1440 大屏:侧栏 280 · 卡片 4 列封顶(auto-fill 260 + 默认封顶)· 正文 78ch 居中(基线已给) */
@media (min-width:1440px){
  :root{--w-side:280px}
}
/* ===== 窄窗口(≤768):侧栏变抽屉、分屏只留一组、标签横向滚动、状态栏精简 ===== */
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
  .side-resizer{display:none}   /* 抽屉态没有可拖的分隔条 */
  /* ★ 触达 ≥44px:chip / 图标按钮 / 标签 / 树项 / 区块筛选 全抬到 44(桌面保持紧凑) */
  .act{width:44px;height:44px}
  .side-head input{height:44px}
  .side-head .chip{min-height:44px;padding:0 var(--s4);font-size:var(--f-sm)}
  body.work .icon-btn{width:44px;height:44px;min-width:44px;min-height:44px}
  .tree-item{min-height:44px}
  .t-close{width:44px;height:44px}
  .statusbar{gap:var(--s2)}
  .tb-title{display:none}
  .group-tabs{scrollbar-width:none}
}
"""
