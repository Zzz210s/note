#!/usr/bin/env python3
"""A11 课件登记口径自检(2026-09-26):每节 `lessons/*.html` 与每张 `reference/*.html`
都必须在工作区 `00-索引.md` 的「## 课程」块里登记。

背景:用户决定舍弃长版词条层(`!名词解释/20-知识/` 已删),判据从「词条必须有课」反过来
变成「**课必须有登记**」—— 课躺在 `lessons/` 里、目录页上看不见,是这次要防的失效。
这里在临时假库里验证新判据该报的报、不该报的不报。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_lessons as S
from selftest_teach import _scaffold

WORK = "10-项目/!名词解释"
LESSON = WORK + "/lessons/0001-测试夹具.html"
CARD = WORK + "/reference/夹具速查.html"
INDEX = WORK + "/00-索引.md"

BLOCK_BOTH = ("---\ntype: note\nstatus: done\n---\n\n# !名词解释(容器)\n\n## 课程\n\n"
              "- 课程地图:暂无(尚未生成课程地图)\n"
              "- 第 1 节:[0001 · 测试夹具](<lessons/0001-测试夹具.html>)\n"
              "- 速查卡:[夹具速查](<reference/夹具速查.html>)\n\n## 入口与出口\n\n- 无\n")
BLOCK_ONLY_LESSON = BLOCK_BOTH.replace("- 速查卡:[夹具速查](<reference/夹具速查.html>)\n", "")
BLOCK_ONLY_CARD = BLOCK_BOTH.replace("- 第 1 节:[0001 · 测试夹具](<lessons/0001-测试夹具.html>)\n", "")
BLOCK_FENCED = ("---\ntype: note\nstatus: done\n---\n\n# 容器\n\n## 课程\n\n```\n"
                "- 第 1 节:[0001](<lessons/0001-测试夹具.html>)\n"
                "- 速查卡:[卡](<reference/夹具速查.html>)\n```\n\n## 入口与出口\n\n- 无\n")


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _fake(root: Path, block: str = BLOCK_BOTH, with_index: bool = True) -> None:
    L.VAULT_ROOT = root
    _scaffold(root, "!名词解释")                       # 容器也是工作区:三件套要齐
    _mk(root, LESSON, "<title>0001 · 测试夹具 · 名词解释</title>\n")
    _mk(root, CARD, "<title>夹具速查</title>\n")
    if with_index:
        _mk(root, INDEX, block)


def test_all_registered_passes():
    """① 课与卡都登记 → 不报。"""
    with tempfile.TemporaryDirectory() as d:
        _fake(Path(d))
        assert not S.check_lessons_registered(), S.check_lessons_registered()


def test_unregistered_lesson_is_reported():
    """② 课没登记(卡登记了)→ 只报这一课,detail 里给出 lessons/ 路径。"""
    with tempfile.TemporaryDirectory() as d:
        _fake(Path(d), BLOCK_ONLY_CARD)
        got = S.check_lessons_registered()
        assert len(got) == 1, got
        assert got[0].stage == "A11" and got[0].path.endswith("0001-测试夹具.html"), got
        assert "lessons/0001-测试夹具.html" in got[0].detail, got[0].detail


def test_unregistered_card_is_reported():
    """③ 速查卡没登记 → 也要报(卡是长期资产,同样得挂到目录页上)。"""
    with tempfile.TemporaryDirectory() as d:
        _fake(Path(d), BLOCK_ONLY_LESSON)
        got = S.check_lessons_registered()
        assert len(got) == 1 and got[0].path.endswith("夹具速查.html"), got


def test_block_inside_code_fence_is_not_registration():
    """④ 把块抄进代码围栏不算登记(`strip_code` 抹白后应报两件)。"""
    with tempfile.TemporaryDirectory() as d:
        _fake(Path(d), BLOCK_FENCED)
        got = S.check_lessons_registered()
        assert len(got) == 2, got


def test_missing_index_is_out_of_scope():
    """⑤ 没有 `00-索引.md` → 不报(缺索引页归 A4,不在这里重复报)。"""
    with tempfile.TemporaryDirectory() as d:
        _fake(Path(d), with_index=False)
        assert not S.check_lessons_registered(), S.check_lessons_registered()


def test_dir_without_lessons_is_out_of_scope():
    """⑥ 既没有 `lessons/` 也没有 `reference/` 的目录不管辖(A11 other 判据的活)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _scaffold(root, "2026-12-掌握SQLite")
        _mk(root, "10-项目/2026-12-掌握SQLite/00-索引.md",
            "---\ntype: project\nstatus: learning\n---\n# 项目\n\n## 课程\n\n- 无\n")
        assert not S.check_lessons_registered(), S.check_lessons_registered()


def test_missing_section_alone_is_reported_by_teach_module():
    """⑦ 整块缺失由 `checks_teach` 报一次(分工:本模块不逐课重复报)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root, "---\ntype: note\nstatus: done\n---\n\n# 容器\n\n## 入口与出口\n\n- 无\n")
        assert len(S.check_lessons_registered()) == 2, S.check_lessons_registered()
        import checks_teach as T
        assert T.check_teach_workspace(), "整块缺失应由 checks_teach 报"


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
