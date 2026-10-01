#!/usr/bin/env python3
"""A15「课件规范」自检(2026-10-01):在临时假库里验证五种判据该报的报、不该报的不报。

判据见 `checks_lesson_rules.py`:① 形态必写且取值三选一 ② 定义节有 `class="plain"`
③ 全文 `class="term"` ≥3 ④ 练习选项(含 hint 备注)不是描述性短语 ⑤ ≤260 行。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_lesson_rules as S

LESSON = "10-项目/!名词解释/lessons/0001-测试夹具.html"

META = '<p class="lesson-meta">名词解释教学工作区 · 课程 0001 · 形态 单概念 · 约 5 分钟</p>\n'
DEF = ('<h2>1 | 定义</h2>\n<p><span class="dfn">测试夹具 fixture:固定环境</span>'
       '<span class="plain">像考试前先把桌子摆好</span></p>\n')
TERMS = ('<h2>2 | 它怎么解决</h2>\n<p><span class="term">夹具</span> '
         '<span class="term">替身</span> <span class="term">桩</span></p>\n')
QUIZ = ('<h2>8 | 练习</h2>\n<div class="quiz" data-answer="a">\n'
        '<button data-key="a">夹具 <small class="hint">先摆好的那套环境</small></button>\n'
        '<button data-key="b">替身</button>\n<button data-key="c">桩</button>\n'
        '<button data-key="d">快照</button>\n</div>\n')
GOOD = META + DEF + TERMS + QUIZ


def _fake(root: Path, body: str = GOOD) -> None:
    L.VAULT_ROOT = root
    p = root / LESSON
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def _one(body: str) -> list:
    """在假库里跑一遍,返回 findings。"""
    with tempfile.TemporaryDirectory() as d:
        _fake(Path(d), body)
        return S.check_lesson_rules()


def test_compliant_lesson_passes():
    """① 合规节 → 一条都不报。"""
    got = _one(GOOD)
    assert not got, got


def test_missing_form_is_reported():
    """② 缺「形态」→ 报一条,指到 .lesson-meta。"""
    got = _one(GOOD.replace(" · 形态 单概念", ""))
    assert len(got) == 1 and got[0].stage == "A15", got
    assert "未标形态" in got[0].detail, got[0].detail
    assert got[0].line == 1, got[0].line


def test_invalid_form_is_reported():
    """③ 形态取值不在三类 → 报一条(取值非法与缺失分开)。"""
    got = _one(GOOD.replace("形态 单概念", "形态 操作型"))
    assert len(got) == 1 and "不在三类里" in got[0].detail, got


def test_missing_plain_is_reported():
    """④ 定义节没有大白话 → 报一条。"""
    got = _one(GOOD.replace('<span class="plain">像考试前先把桌子摆好</span>', ""))
    assert len(got) == 1 and "plain" in got[0].detail, got


def test_term_below_min_is_reported():
    """⑤ 全文 term 只剩 1 处 → 报一条。"""
    got = _one(GOOD.replace('<span class="term">替身</span> <span class="term">桩</span>', ""))
    assert len(got) == 1 and "class=\"term\"" in got[0].detail, got
    assert "只有 1 处" in got[0].detail, got[0].detail


def test_option_description_is_reported():
    """⑥ 选项正文写成描述性短语 → 报一条并指到那一行。"""
    got = _one(GOOD.replace('<button data-key="b">替身</button>',
                            '<button data-key="b">定好问什么、答什么的那一层</button>'))
    assert len(got) == 1 and "描述性短语" in got[0].detail, got
    assert got[0].line == 9, got[0].line  # 第 9 行 = 那个按钮


def test_hint_description_is_reported():
    """⑦ 描述性短语藏在 <small class="hint"> 里 → 一样要报。"""
    got = _one(GOOD.replace('<small class="hint">先摆好的那套环境</small>',
                            '<small class="hint">定好问什么、答什么的那一层</small>'))
    assert len(got) == 1 and "描述性短语" in got[0].detail, got


def test_over_max_lines_is_reported():
    """⑧ 超过 260 行 → 报一条。"""
    got = _one(GOOD + "\n" * 300)
    assert len(got) == 1 and "上限 260" in got[0].detail, got


def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print("FAIL %s: %s" % (t.__name__, e))
        else:
            print("PASS %s" % t.__name__)
            passed += 1
    print("PASS=%d/%d" % (passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(_run())
