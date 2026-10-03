#!/usr/bin/env python3
"""0-Note 在线阅读站 · 正文排版(卡片内长文)。

卡片默认样式是"摘要卡",而站点的对外页/全库页要把笔记正文**内联**进卡片,所以这里
单独给 `.card-body` 一套正文排版(标题层次、段落、列表、表格、代码、引用、双链),
不动 `site_css.py`(那份已评审冻结)。渲染时 `render_page` 用 `site_css.CSS + PROSE`。
"""
from __future__ import annotations

PROSE = """
/* 卡片内正文:与摘要卡共存的排版区 */
.card-body{margin-top:.6rem;padding-top:.55rem;border-top:1px dashed var(--divider);font-size:var(--f-base);line-height:1.75}
.card-body>*:first-child{margin-top:0}
.card-body h2{font-size:1.02rem;margin:1.1rem 0 .45rem;font-weight:700}
.card-body h3{font-size:.95rem;margin:.95rem 0 .4rem;font-weight:600}
.card-body h4,.card-body h5,.card-body h6{font-size:.9rem;margin:.85rem 0 .35rem;font-weight:600;color:var(--t2)}
.card-body p{margin:.5rem 0}
.card-body ul,.card-body ol{margin:.5rem 0 .5rem 1.15rem;padding:0}
.card-body li{margin:.22rem 0}
.card-body li>ul,.card-body li>ol{margin-top:.22rem}
.card-body blockquote{margin:.6rem 0;padding:.35rem .8rem;border-left:3px solid var(--divider);color:var(--t2)}
.card-body blockquote p{margin:.25rem 0}
.card-body hr{margin:.9rem 0;border:0;border-top:1px solid var(--divider)}
.card-body code{font-family:var(--mono);font-size:.88em;background:var(--bg-mute);border-radius:4px;padding:.05rem .28rem}
.card-body pre{margin:.6rem 0;padding:.6rem .75rem;background:var(--bg-mute);border-radius:var(--radius);overflow-x:auto}
.card-body pre code{background:none;padding:0;font-size:.86em;line-height:1.6}
.card-body table{margin:.6rem 0;border-collapse:collapse;font-size:.9em;width:100%;display:block;overflow-x:auto}
.card-body th,.card-body td{border:1px solid var(--divider);padding:.32rem .55rem;text-align:left;vertical-align:top}
.card-body th{background:var(--bg-alt);font-weight:600}
.card-body a,.card-body .wl{color:var(--brand)}
.card-body .wl{border-bottom:1px dotted var(--brand)}
.card-body strong{font-weight:700}
.card-body sub,.card-body sup{font-size:.78em}
/* 卡片必须能被压缩:grid/flex 项默认 min-width:auto,正文里的宽表格/长路径会把卡片撑破 */
.cards>.card{min-width:0;max-width:100%}
.card-head{min-width:0;flex-wrap:wrap}
.card-body,.card-sum,.card-win,.card-title{overflow-wrap:anywhere}
.card-body table{max-width:100%}
.card-body pre{max-width:100%}
/* 图标按钮统一到 44px 触达(spec 6.5);正文里的行内链接不在此列 */
.icon-btn{min-width:44px;min-height:44px}
"""
