#!/usr/bin/env python3
"""0-Note 巡检 A15「课件规范」:按三形态模板核对《!名词解释》的课。

口径与样板守门员(2026-10-01 三形态验收)对齐,只是搬到真库、逐节机械判:

  ① `.lesson-meta` 必写「形态 单概念|对比组|体系图」;缺了或取值非法即报。
  ② 第 1 节「定义」里必须有 `class="plain"`(大白话,生活锚点,不复述定义)。
  ③ 全文 `class="term"` ≥3(正文首次出现的关键名词要能单独识别)。
  ④ 练习选项(**含** `<small class="hint">` 备注)不许写成描述性短语
     (「的那一层 / 的那种 / 那一层」这类),要写术语原名。
  ⑤ 课 ≤260 行。

范围:模板体系当前只铺到容器 `10-项目/!名词解释`(设计 §3.10:其余技能项目
「按形态补齐」排在后续阶段),故 A15 只扫它 `lessons/*.html` —— 与铺开计划 A-1
「21 节课全部合规 = A15 全 0」同一口径。要扩到全库课件,把工作区加进
`SCOPED_WORKSPACES` 即可。

输出与其它检查一致:每条 `路径:行号 说明`,行号 0 = 整篇级。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

FORMS = ("单概念", "对比组", "体系图")
# 已采用三形态模板的工作区(设计 §3.10 的后续阶段逐个加进来)
SCOPED_WORKSPACES = ("!名词解释",)
LESSONS_DIR = "lessons"
MAX_LINES = 260
MIN_TERM = 3

META_RE = re.compile(r'''class\s*=\s*["'][^"']*lesson-meta[^"']*["'][^>]*>(.*?)</p>''', re.S)
FORM_RE = re.compile(r"形态[:：\s]*?([^·<>\s]+)")
H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|\Z)", re.S)
NUM_RE = re.compile(r"^\s*\d+\s*[|｜]\s*")
TAG_RE = re.compile(r"<[^>]+>")
PLAIN_RE = re.compile(r'''class\s*=\s*["'][^"']*\bplain\b''')
TERM_RE = re.compile(r'''class\s*=\s*["'][^"']*\bterm\b''')
BUTTON_RE = re.compile(r"<button\b[^>]*>(.*?)</button>", re.S)
DESC_RE = re.compile(r"的那一层|的那种|那一层")


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _strip(s: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub("", s)).strip()


def _lesson_files(root: Path | None = None) -> list[Path]:
    root = Path(root) if root is not None else L.VAULT_ROOT
    out: list[Path] = []
    for work in SCOPED_WORKSPACES:
        d = root / L.PROJECT_ROOT / work / LESSONS_DIR
        if d.is_dir():
            out.extend(sorted(d.glob("*.html")))
    return out


def _form(text: str) -> tuple[str | None, int]:
    """`.lesson-meta` 里的形态原值 + 该段行号;没写形态返回 (None, 行号/0)。"""
    m = META_RE.search(text)
    if not m:
        return None, 0
    fm = FORM_RE.search(m.group(1))
    return (fm.group(1) if fm else None), _line_of(text, m.start())


def _def_body(text: str) -> tuple[str, int]:
    """第 1 节「定义」的正文与行号;先抹白代码块,免得抄示例过关。"""
    stripped = L.strip_code(text)
    for m in H2_RE.finditer(stripped):
        if NUM_RE.sub("", _strip(m.group(1))).strip() == "定义":
            return m.group(2), _line_of(stripped, m.start())
    return "", 0


def _check_one(rel: str, text: str) -> list[L.Finding]:
    out: list[L.Finding] = []
    form, meta_line = _form(text)
    if not form:
        out.append(L.Finding("A15", rel, meta_line,
                             ".lesson-meta 未标形态(需「形态 单概念|对比组|体系图」)"))
    elif form not in FORMS:
        out.append(L.Finding("A15", rel, meta_line,
                             "形态「%s」不在三类里(%s)" % (form, "/".join(FORMS))))
    body, def_line = _def_body(text)
    if not PLAIN_RE.search(body):
        out.append(L.Finding("A15", rel, def_line,
                             '第 1 节「定义」缺 class="plain"(大白话)'))
    n = len(TERM_RE.findall(text))
    if n < MIN_TERM:
        out.append(L.Finding("A15", rel, 0,
                             '全文 class="term" 只有 %d 处(要求 ≥%d)' % (n, MIN_TERM)))
    for m in BUTTON_RE.finditer(text):
        opt = _strip(m.group(1))
        if DESC_RE.search(opt):
            out.append(L.Finding("A15", rel, _line_of(text, m.start()),
                                 "练习选项「%s」是描述性短语,要写术语原名" % opt))
    lines = len(text.splitlines())
    if lines > MAX_LINES:
        out.append(L.Finding("A15", rel, 0, "课 %d 行(上限 %d)" % (lines, MAX_LINES)))
    return out


def check_lesson_rules(root: Path | None = None) -> list[L.Finding]:
    """A15:逐节核对课件规范。"""
    out: list[L.Finding] = []
    for f in _lesson_files(root):
        out.extend(_check_one(L.rel_path(f), L.read_text(f)))
    return out


if __name__ == "__main__":
    for f in check_lesson_rules():
        print("%s:%s %s" % (f.path, f.line, f.detail))
