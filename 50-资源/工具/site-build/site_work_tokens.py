#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台视觉 token(拾枝刻度)。

视觉令牌与拾枝(`F:/0-code/20-active/LifeLog/src/shared/theme.css`)同源 —— 只取刻度与配色,
不引它的架构。`TOKENS` 由 `WORK_CSS` 拼在最前,对后续所有模块(site_css / PROSE / SIDE_CSS /
PANEL_CSS / STATES_CSS)都可见(CSS 自定义属性按 computed value 解析,声明先后不影响取值)。

刻度(设计 spec §4):间距 8 档 2/4/6/8/12/16/24/32;字号 7 档 11/12/13/14/15/16/20
(600 只给 title 与 card);圆角 4 档 4/6/8/12(按浮起程度递增);阴影**只有浮层用**;
动效 100/150/220ms + ease-out;图标统一 16px。

三层方向与拾枝一致(与 VS Code 相反):**chrome(侧栏/活动栏/标签栏/标题栏)最亮,
canvas(编辑区)次之,raised(卡片/输入/浮层)回到最亮**。旧令牌名保留为别名,指向新档,
这样 10 个样式模块不必改名(例如 `--w-side-bg` → `--w-chrome`、`--w-editor` → `--w-canvas`)。

零外部资源:无 @import、无字体/图标库。色值白名单见 `selftest_tokens.py`。
"""
from __future__ import annotations

TOKENS = r"""
/* ===== 刻度:间距 / 字号 / 圆角 / 外壳尺寸 / 阴影 / 动效 / 图标 ===== */
:root{
  --s0:2px; --s1:4px; --s6:6px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s7:32px;
  --f-xs:11px; --f-sm:12px; --f-md:13px; --f-body-sm:14px; --f-base:15px; --f-card:16px; --f-title:20px;
  --r-xs:4px; --r-ctl:6px; --r-card:8px; --r-frame:8px; --r-float:12px; --icon:16px;
  /* 外壳尺寸:活动栏 48 · 侧栏 260(可拖 200-420)· 标签栏 32 · 状态栏 24 · 标题栏 35 */
  --w-activity:48px; --w-side:260px; --w-tab:32px; --w-status:24px; --w-title:35px;
  /* 阴影:只有浮层用(chrome 靠边框分,卡片靠表面 + 极轻边框) */
  --sh-1:0 1px 2px rgba(0,0,0,.06);
  --sh-2:0 4px 12px rgba(0,0,0,.10);
  --sh-3:0 8px 24px rgba(0,0,0,.16);
  --dur-fast:100ms; --dur-base:150ms; --dur-slow:220ms;
  --ease-out:cubic-bezier(.22,1,.36,1);
  --w-font:var(--font,ui-sans-serif,system-ui,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif);
}
/* ===== 亮色(拾枝):chrome 白 / canvas 浅灰 / raised 白 · 单一强调色 #2563eb ===== */
body.work{
  --w-canvas:#f6f6f7; --w-chrome:#ffffff; --w-chrome-alt:#ececee; --w-raised:#ffffff;
  --w-hover:#efeff1; --w-sel:#e8f1fd; --w-line:#e3e5e8; --w-line-strong:#cfd4d9;
  --w-t1:#1f2328; --w-t2:#5e666f; --w-t3:#7e868f;
  --w-accent:#2563eb; --w-accent-text:#1d4ed8; --w-accent-soft:#e8f1fd;
  /* 旧名别名(旧站调用点;必须放在 body.work —— var() 在声明处解析) */
  --bg:var(--w-canvas); --bg-alt:var(--w-chrome); --bg-elv:var(--w-raised);
  --bg-mute:var(--w-hover); --divider:var(--w-line);
  --t1:var(--w-t1); --t2:var(--w-t2); --t3:var(--w-t3);
  --brand:var(--w-accent); --brand-2:var(--w-c-project); --brand-soft:var(--w-accent-soft);
  --mark-fg:var(--w-t1);
  --c-course:var(--w-c-course); --c-course-soft:var(--w-c-course-soft);
  --c-know:var(--w-c-know); --c-know-soft:var(--w-c-know-soft);
  --c-project:var(--w-c-project); --c-project-soft:var(--w-c-project-soft);
  --c-log:var(--w-c-log); --c-log-soft:var(--w-c-log-soft);
  --c-index:var(--w-t2); --c-index-soft:var(--w-hover);
  --s-learning:var(--w-accent); --s-learning-soft:var(--w-accent-soft);
  --s-todo:var(--w-c-log); --s-todo-soft:var(--w-c-log-soft);
  --s-done:var(--w-c-know); --s-done-soft:var(--w-c-know-soft);
  --s-idle:var(--w-t2); --s-idle-soft:var(--w-hover);
  --shadow:var(--sh-1);
  /* 旧名别名(指向新档;样式模块沿用旧名即可,勿逐个改名) */
  --w-bg:var(--w-canvas); --w-editor:var(--w-canvas); --w-side-bg:var(--w-chrome);
  --w-input:var(--w-raised); --w-focus:var(--w-accent); --w-active:var(--w-sel);
  --w-status-bg:var(--w-accent); --w-status-fg:#ffffff;
  --w-overlay:rgb(0 0 0 / 30%);
  --w-c-course:var(--w-accent); --w-c-course-soft:var(--w-accent-soft);
  --w-c-know:#16a34a; --w-c-know-soft:#f1f8f3;
  --w-c-log:#b45309; --w-c-log-soft:#fdf6ec;
  --w-c-project:#5e666f; --w-c-project-soft:#f0f1f2;
}
/* ===== 暗色(VS Code Dark+,与拾枝同):chrome 略亮 / canvas 最暗 ===== */
[data-theme=dark] body.work,body.work[data-theme=dark]{
  --w-canvas:#1e1e1e; --w-chrome:#252526; --w-chrome-alt:#2d2d30; --w-raised:#252526;
  --w-hover:#2a2d2e; --w-sel:#264f78; --w-line:#3c3c3c; --w-line-strong:#4a4a4a;
  --w-t1:#cccccc; --w-t2:#9d9d9d; --w-t3:#7a7a7a;
  --w-accent:#007acc; --w-accent-text:#60caff; --w-accent-soft:#264f78;
  --w-status-fg:#ffffff;
  --w-overlay:rgb(0 0 0 / 55%);
  --sh-1:0 1px 2px rgba(0,0,0,.24);
  --sh-2:0 4px 12px rgba(0,0,0,.30);
  --sh-3:0 8px 24px rgba(0,0,0,.36);
  --w-c-course:var(--w-accent); --w-c-course-soft:var(--w-accent-soft);
  --w-c-know:#89d185; --w-c-know-soft:#22301f;
  --w-c-log:#cca700; --w-c-log-soft:#332c14;
  --w-c-project:#9d9d9d; --w-c-project-soft:#2a2d2e;
}
"""
