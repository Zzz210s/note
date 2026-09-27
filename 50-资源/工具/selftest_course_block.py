#!/usr/bin/env python3
"""课程块「已掌握」标记的自检(2026-09-26 加)。

口径:`00-索引.md` 的课程块里,每节课后面可以带 ` — 已掌握 <日期>`,来源**只能是**
`learning-records/*.md`(teach 技能的学习记录)—— 不是手写的状态列,也不是"读完了"。
所以这里验证三件事:

1. 有记录、记录里点名了课号 → 那一行带标记,日期取自记录的 `Date:`;
2. 记录里提到的数字**不是真实课号** → 不标记(避免把日期、页码当课号);
3. 没有 `learning-records/` → 一行标记都不加(现状如此)。

不改真库:全程在临时目录里造一个假的课程工作区。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_indexes_render as G


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _lesson(proj: Path, num: str, title: str) -> None:
    _mk(proj, "lessons/%s-x.html" % num,
        "<html><head><title>%s · x · 名词解释</title></head><body></body></html>" % title)


def _record(proj: Path, name: str, body: str) -> None:
    _mk(proj, "learning-records/%s" % name, body)


def _lines(proj: Path) -> list[str]:
    return G.course_block(proj)


def _line_for(lines: list[str], num: str) -> str:
    return next(l for l in lines if "lessons/%s-" % num in l)


def test_record_marks_lesson_with_date():
    """① 记录点名 0013、带 Date → 那一行是「— 已掌握 2026-09-26」。"""
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _lesson(proj, "0013", "前端 / 后端 / 接口")
        _lesson(proj, "0014", "Kubernetes")
        _record(proj, "0001-0013-前端后端接口.md",
                "---\nDate: 2026-09-26\n---\n# 能说清前端、后端、接口各自在哪跑\n\n不看选项说出了三块地盘的分工。\n")
        lines = _lines(proj)
        l13 = _line_for(lines, "0013")
        assert "已掌握 2026-09-26" in l13, l13
        assert "已掌握" not in _line_for(lines, "0014"), _line_for(lines, "0014")


def test_record_without_date_still_marks():
    """② 记录没有 Date → 仍算掌握,但只写「已掌握」,不编日期。"""
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _lesson(proj, "0015", "Gradle")
        _record(proj, "0001-0015-gradle.md", "# 我本来就会 Gradle\n\n声明式任务图这点早就熟了。\n")
        line = _line_for(_lines(proj), "0015")
        assert "已掌握" in line and "2026" not in line, line


def test_date_number_is_not_mistaken_for_lesson():
    """③ 记录里只出现日期 2026-09-26,没有真实课号 → 不做任何标记。"""
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _lesson(proj, "0016", "静态部署")
        _record(proj, "0001-学了一点.md", "---\nDate: 2026-09-26\n---\n# 随便记一句\n\n今天看了些东西。\n")
        line = _line_for(_lines(proj), "0016")
        assert "已掌握" not in line, line


def test_no_records_dir_means_no_marks():
    """④ 没有 `learning-records/` → 课程块里一个「已掌握」都没有(真库现状)。"""
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _lesson(proj, "0017", "SSG")
        lines = _lines(proj)
        assert not any("已掌握" in l for l in lines), lines
        assert "学习记录:暂无" in "\n".join(lines)


def test_lesson_link_name_is_intact():
    """⑤ 标记是后缀,不能破坏 A11 的判定(`f.name in 课程块`)。"""
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _lesson(proj, "0018", "树莓派")
        _record(proj, "0001-0018-树莓派.md", "---\nDate: 2026-09-26\n---\n# 板子那一套\n\n分清了单板机与单片机。\n")
        lines = _lines(proj)
        assert any("0018-x.html" in l for l in lines), lines
        assert "0018-x.html>) — 已掌握 2026-09-26" in _line_for(lines, "0018"), _line_for(lines, "0018")


def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print("FAIL %s: %s" % (t.__name__, e))
        else:
            print("PASS %s" % t.__name__)
            ok += 1
    print("PASS=%d/%d" % (ok, len(tests)))
    return 0 if ok == len(tests) else 1


if __name__ == "__main__":
    sys.exit(_run())
