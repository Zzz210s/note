#!/usr/bin/env python3
"""0-Note 巡检扩展:A11 的一条 —— 每节课都要在目录页上登记。

2026-09-26 起:这条判据原来是「容器的每篇词条都要有课」(见 git 历史里的
`check_glossary_lessons`)。用户决定**完全舍弃长版词条层**(`!名词解释/20-知识/` 已删除),
内容改由「课」承载 —— 于是判据反过来以**课件为准**:

- 工作区里有 `lessons/*.html`,那每个文件都必须出现在该工作区 `00-索引.md` 的
  `## 课程` 块里(块内写成相对路径链接,如 `lessons/0005-测试夹具.html`)。
- 只查"有没有登记",**不查块本身在不在**:缺 `## 课程` 块那份判据在 `checks_teach.py`
  (整块缺失只报一次,不逐课重复报)。缺 `00-索引.md` 归 A4,这里不报。
- 学习项目与容器(`!名词解释`)同一套判据:只要它建了课件,就必须挂到目录页上。

2026-10-01 起**速查卡模块退役**(用户裁定「速查表认为无用了,这个模块可以删除」):
`!名词解释/reference/` 下的卡已全部删除,`reference/` 只剩「课程地图」这类非卡文件,
此后 `reference/` 下的文件**不再要求登记** —— 判据只认 `lessons/*.html`。

判据刻意"宁缺勿滥":只报**确定没登记**的文件(按文件名精确匹配课程块正文),
不猜测改名、不比对相似名 —— 相似名匹配会被"课程地图"这类文件名带偏。
"""
from __future__ import annotations

import pathlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

COURSE_SECTION_RE = re.compile(r"^## 课程\s*$", re.M)
LESSONS_DIR = "lessons"


def _course_section(text: str) -> str:
    """`## 课程` 块的正文(到下一个 `##` 标题或文末);先抹白代码块,免得抄示例过关。"""
    stripped = L.strip_code(text)
    m = COURSE_SECTION_RE.search(stripped)
    if not m:
        return ""
    rest = stripped[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def _workspaces() -> list[Path]:
    """建了课件(`lessons/`)的 `10-项目/<目录>`。"""
    base = L.VAULT_ROOT / L.PROJECT_ROOT
    out = []
    for p in sorted(base.iterdir()) if base.is_dir() else []:
        if p.is_dir() and (p / LESSONS_DIR).is_dir():
            out.append(p)
    return out


def check_lessons_registered() -> list[L.Finding]:
    """A11:每节课都必须在工作区 `00-索引.md` 的「## 课程」块里登记。"""
    out: list[L.Finding] = []
    for work in _workspaces():
        index = work / L.PROJECT_INDEX
        if not index.exists():
            continue  # 缺索引页归 A4
        section = _course_section(L.read_text(index))
        for f in sorted((work / LESSONS_DIR).glob("*.html")):
            if f.name in section:
                continue
            out.append(L.Finding("A11", L.rel_path(f), 0,
                                 "未在目录页「## 课程」块登记(路径:%s/%s)"
                                 % (LESSONS_DIR, f.name)))
    return out
