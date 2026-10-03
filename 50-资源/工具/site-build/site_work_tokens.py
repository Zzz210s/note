#!/usr/bin/env python3
"""0-Note 在线阅读站 · 工作台视觉 token(标尺 + 亮暗配色)。

从 `site_work_css` 拆出(该表加 token 后触 200 行上限)。`TOKENS` 由 `WORK_CSS` 拼在最前,
对后续所有模块(site_css / PROSE / SIDE_CSS / PANEL_CSS / STATES_CSS)都可见 —— CSS 自定义
属性按 computed value 解析,声明先后不影响 `var()` 取值。

标尺(设计 §7):间距只 5 档 4/8/12/16/24;字号只 6 档 11.5/12.5/13/15/15.5/20;圆角 6/10/8;
阴影只一层极轻;图标统一 16px。语义色(课程/笔记/记录/项目 + 强调 + 强调浅底)亮暗各一套,
亮色白底深字、暗色 slate 底浅字;badge 文字对 `-soft` 底的对比度全部 ≥4.5(亮色取 6% 淡底、
暗色取 12% 淡底;算式见 task-6-report.md)。零外部资源:无 @import、无字体/图标库。
"""
from __future__ import annotations

TOKENS = r"""
/* ===== 标尺:间距 / 字号 / 圆角 / 阴影 / 图标 ===== */
:root{
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px;
  --f-xs:11.5px; --f-sm:12.5px; --f-md:13px; --f-base:15px; --f-card:15.5px; --f-title:20px;
  --r-ctl:6px; --r-card:10px; --r-frame:8px; --icon:16px;
  /* 外壳尺寸(VS Code 口径):活动栏 48 · 侧栏 260 · 标签栏 35 · 状态栏 24 · 标题栏 35 */
  --w-activity:48px; --w-side:260px; --w-tab:35px; --w-status:24px; --w-title:35px;
  --sh-1:0 1px 2px rgba(16,24,40,.07);
  --w-font:var(--font,ui-sans-serif,system-ui,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif);
}
/* ===== 亮色(默认):白编辑区 / 浅灰侧栏 / 蓝强调 ===== */
body.work{
  --w-bg:#ffffff; --w-side-bg:#f3f4f6; --w-editor:#ffffff; --w-line:#e1e4e8;
  --w-hover:#eceef1; --w-sel:#e3e8f0; --w-active:#e3e8f0;
  --w-t1:#1f2328; --w-t2:#57606a; --w-t3:#69707d;
  --w-accent:#0b62d0; --w-accent-soft:rgba(11,98,208,.10); --w-focus:#0b62d0; --w-input:#ffffff;
  --w-status-bg:#0b62d0; --w-status-fg:#ffffff;
  --w-c-course:#0b62d0; --w-c-course-soft:#f0f6fc;
  --w-c-know:#1a7f37; --w-c-know-soft:#f1f7f3;
  --w-c-log:#bc4c00; --w-c-log-soft:#fbf4f0;
  --w-c-project:#8250df; --w-c-project-soft:#f8f5fd;
}
/* ===== 暗色:slate 三层(底 / 侧栏 / 边框)+ 浅字 ===== */
[data-theme=dark] body.work,body.work[data-theme=dark]{
  --w-bg:#0f172a; --w-side-bg:#1e293b; --w-editor:#0f172a; --w-line:#334155;
  --w-hover:#243044; --w-sel:#334155; --w-active:#334155;
  --w-t1:#f8fafc; --w-t2:#94a3b8; --w-t3:#8494a7;
  --w-accent:#58a6ff; --w-accent-soft:rgba(88,166,255,.16); --w-focus:#58a6ff; --w-input:#1e293b;
  --w-status-bg:#1e293b; --w-status-fg:#58a6ff;
  --w-c-course:#58a6ff; --w-c-course-soft:#1b2e4c;
  --w-c-know:#3fb950; --w-c-know-soft:#16301f;
  --w-c-log:#f0883e; --w-c-log-soft:#3a2c14;
  --w-c-project:#c4a7ff; --w-c-project-soft:#2a2444;
}
"""
