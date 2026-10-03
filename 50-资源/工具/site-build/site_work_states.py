#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台控件四态补全(悬停 / 聚焦 / 按下 / 禁用)。

由 `site_render` 内联在 PANEL_CSS 之后(**最后一个样式段**,同权重时压过前面各表)。
悬停大多已在各模块里就近定义;聚焦环由 `WORK_CSS` 的 `body.work :focus-visible` 统一给
(亮 `#0b62d0` / 暗 `#58a6ff`,对相邻底 ≥3:1);这里补齐「按下」(背景降一档到 `--w-active`)
与「禁用」(降不透明度 + `cursor:not-allowed`),并补 `.link-btn` / `.view-btn` / `.sec-filter`
缺失的悬停。覆盖清单(设计 §7):`.act .icon-btn .tab .tree-item .chip .st-item .link-btn
.view-btn .sec-toggle`(+ 同族的 `.sec-filter`)。零外部资源。
"""
from __future__ import annotations

STATES_CSS = r"""
/* ===== 按下:背景降一档 ===== */
body.work .act:active,body.work .icon-btn:active,body.work .tab:active,body.work .tree-item:active,
body.work .chip:active,body.work .view-btn:active,body.work .sec-toggle:active,
body.work .sec-filter:active,body.work .link-btn:active{background:var(--w-active)}
/* ===== 禁用:降透明度 + 禁止光标 ===== */
body.work .act:disabled,body.work .icon-btn:disabled,body.work .tab:disabled,body.work .tree-item:disabled,
body.work .chip:disabled,body.work .view-btn:disabled,body.work .sec-toggle:disabled,
body.work .sec-filter:disabled,body.work .link-btn:disabled,
body.work .statusbar .st-item:disabled{opacity:.45;cursor:not-allowed}
/* ===== 补齐缺失的悬停 ===== */
body.work .link-btn:hover{color:var(--w-accent);text-decoration:underline}
body.work .view-btn:hover{color:var(--w-t1);border-color:var(--w-t2)}
body.work .sec-filter:hover{color:var(--w-t1)}
body.work .chip:hover{border-color:var(--w-accent);color:var(--w-t1)}
"""
