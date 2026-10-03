#!/usr/bin/env python3
"""工作台视觉自检:标尺 token / 间距 / 字号 / 语义色 / 图标 / 四态(含一条负向)。

从 `selftest_work` 拆出(该文件将触 200 行)。读的是各 CSS 模块的**源码字符串**,不渲染。
口径(设计 §7):间距只 5 档 4/8/12/16/24;字号只 6 档 11.5/12.5/13/15/15.5/20;工作台各表
不出现间距 / 字号 px 魔数;六个语义色亮暗各一套;图标统一 16px / 1.5px 描边;九个控件四态齐全。
单跑:`PYTHONIOENCODING=utf-8 python -B selftest_tokens.py`
"""
from __future__ import annotations

import re
import sys

import site_css
import site_css_prose
import site_parts
import site_side
import site_work_css
import site_work_panels_css
import site_work_side_css
import site_work_states
import site_work_status_css
import site_work_tokens

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SPACING_OK = {"4px", "8px", "12px", "16px", "24px"}
FONT_OK = {"11.5px", "12.5px", "13px", "15px", "15.5px", "20px"}
SPACING_DECL = re.compile(r"(?:padding|margin|gap)(?:-[a-z]+)?:\s*([^;{}]+)")
FONT_DECL = re.compile(r"font-size:\s*([^;{}]+)")
PX = re.compile(r"[0-9.]+px")
SEMANTIC = ["--w-accent", "--w-accent-soft", "--w-c-course", "--w-c-course-soft",
            "--w-c-know", "--w-c-know-soft", "--w-c-log", "--w-c-log-soft",
            "--w-c-project", "--w-c-project-soft"]
STATES = [".act", ".icon-btn", ".tab", ".tree-item", ".chip", ".st-item",
          ".link-btn", ".view-btn", ".sec-toggle"]
SCALE = {"--s1": "4px", "--s2": "8px", "--s3": "12px", "--s4": "16px", "--s5": "24px",
         "--f-xs": "11.5px", "--f-sm": "12.5px", "--f-md": "13px", "--f-base": "15px",
         "--f-card": "15.5px", "--f-title": "20px", "--r-ctl": "6px", "--r-card": "10px",
         "--r-frame": "8px", "--icon": "16px"}


def literals(css: str, decl_re: re.Pattern) -> set[str]:
    """取一个 CSS 串里所有「间距 / 字号」声明中的 px 字面量(带 var() 的不算)。"""
    out: set[str] = set()
    for val in decl_re.findall(css):
        out.update(PX.findall(val))
    return out


def workbench_css() -> str:
    """WORK_CSS 末尾已拼 STATUS_CSS;再拼侧栏 / 面板 / 四态,得到实际内联的全部工作台样式。"""
    return (site_work_css.WORK_CSS + site_work_side_css.SIDE_CSS
            + site_work_panels_css.PANEL_CSS + site_work_states.STATES_CSS)


def run(ok) -> None:
    wb = workbench_css()
    site = site_css.CSS + site_css_prose.PROSE

    sp = literals(wb, SPACING_DECL)
    ok("工作台间距无 px 魔数(全部走 var(--sN))", sp <= SPACING_OK, "越界:%s" % sorted(sp - SPACING_OK))
    fs = literals(wb, FONT_DECL)
    ok("工作台字号无 px 魔数(全部走 var(--f-*))", fs <= FONT_OK, "越界:%s" % sorted(fs - FONT_OK))
    sp2 = literals(site, SPACING_DECL)
    ok("站点/正文间距 ⊆ 标尺", sp2 <= SPACING_OK, "越界:%s" % sorted(sp2 - SPACING_OK))
    fs2 = literals(site, FONT_DECL)
    ok("站点/正文字号 ⊆ 标尺", fs2 <= FONT_OK, "越界:%s" % sorted(fs2 - FONT_OK))

    tok = site_work_tokens.TOKENS
    missing = [k for k, v in SCALE.items() if ("%s:%s" % (k, v)) not in tok]
    ok("标尺 token 五档间距 / 六档字号 / 三档圆角 / 图标 16 全定义", not missing, "缺:%s" % missing)

    light = tok[:tok.index("[data-theme=dark]")]
    dark = tok[tok.index("[data-theme=dark]"):]
    miss_l = [n for n in SEMANTIC if ("%s:" % n) not in light]
    miss_d = [n for n in SEMANTIC if ("%s:" % n) not in dark]
    ok("六个语义色亮暗成对(4 类 + 强调 + 强调浅底,各带 -soft)", not miss_l and not miss_d,
       "亮缺:%s 暗缺:%s" % (miss_l, miss_d))

    bad = wb.replace("padding:0 var(--s2) 0 var(--s3)", "padding:0 7px", 1)
    got = literals(bad, SPACING_DECL)
    ok("负向:把 padding 改成 7px 会被标尺检查拦下", "7px" in got and not (got <= SPACING_OK), str(sorted(got)))

    icons = dict(site_parts.ICON)
    icons.update({k: getattr(site_side, k) for k in dir(site_side) if k.startswith("ICON_")})
    bad_icon = [n for n, svg in icons.items()
                if 'class="icon' not in svg or "viewBox=" not in svg or " width=" in svg or " height=" in svg]
    ok("图标全部 class=icon + viewBox,无内联宽高(尺寸归 CSS)", not bad_icon, "违规:%s" % bad_icon)
    ok("图标统一 16px / 1.5px 描边",
       "stroke-width:1.5" in wb and ".act .icon{width:22px" not in wb and "--icon:16px" in tok)

    miss_state = []
    for cls in STATES:
        if any(("%s:%s" % (cls, s)) not in wb for s in ("hover", "active", "disabled")):
            miss_state.append(cls)
    ok("九个控件四态齐全(悬停 / 聚焦 / 按下 / 禁用)", not miss_state, "缺:%s" % miss_state)
    ok("聚焦环统一 body.work :focus-visible + --w-focus", "body.work :focus-visible{outline:2px solid var(--w-focus)" in wb)


if __name__ == "__main__":
    passed = failed = 0

    def _ok(name, cond, detail=""):
        global passed, failed
        if cond:
            passed += 1
            print("PASS", name)
        else:
            failed += 1
            print("FAIL", name, detail)

    run(_ok)
    sp = literals(workbench_css(), SPACING_DECL)
    fs = literals(workbench_css(), FONT_DECL)
    print("工作台间距字面量:%s" % (sorted(sp) or "(无,全 token)"))
    print("工作台字号字面量:%s" % (sorted(fs) or "(无,全 token)"))
    print("结论:%s(%d 例,%d 失败)" % ("PASS" if not failed else "FAIL", passed + failed, failed))
    sys.exit(1 if failed else 0)
