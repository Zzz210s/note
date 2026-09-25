#!/usr/bin/env python3
"""A11 容器口径自检(2026-09-25 Task 14-B):`!名词解释` 的词条必须有课、课要登记在索引上。

背景:`!名词解释` 是容器(没有 `!项目说明.md`),走不到 `check_teach_workspace` 的项目循环 ——
于是「有名词笔记、没开课」没人守。这里在临时假库里验证新判据该报的报、不该报的不报。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_teach as T

NOTE = "10-项目/!名词解释/20-知识/测试夹具是什么.md"
LESSON = "10-项目/!名词解释/lessons/0001-测试夹具.html"
INDEX = "10-项目/!名词解释/00-索引.md"
BLOCK = ("---\ntype: note\nstatus: done\n---\n\n# !名词解释(容器)\n\n## 课程\n\n"
         "- 课程地图:暂无(尚未生成课程地图)\n"
         "- 第 1 节:[0001 · 测试夹具 · 名词解释](<lessons/0001-测试夹具.html>)\n"
         "- 速查卡:暂无(按需由 teach 技能生成)\n"
         "- 学习记录:暂无(按技能规则,只有被证实掌握后才写)\n\n## 入口与出口\n\n- 无\n")


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _fake(root: Path) -> None:
    L.VAULT_ROOT = root
    _mk(root, NOTE, "---\ntype: concept\nstatus: done\n---\n# 测试夹具\n")
    _mk(root, LESSON, "<title>0001 · 测试夹具 · 名词解释</title>\n")
    _mk(root, INDEX, BLOCK)


def test_note_with_lesson_and_registered_passes():
    """① 笔记有课、课也登记在索引里 → 不报。注意词条名比课件名长(`是什么` 后缀),靠双向包含判。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        assert not T.check_glossary_lessons(), T.check_glossary_lessons()


def test_note_without_lesson_is_reported():
    """② 词条在 `20-知识/` 里、`lessons/` 里却没有对应的课 → 报「没有对应课程」。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        (root / LESSON).unlink()
        got = T.check_glossary_lessons()
        assert len(got) == 1 and "没有对应课程" in got[0].detail, got
        assert got[0].path == NOTE and got[0].stage == "A11", got


def test_lesson_not_registered_is_reported():
    """③ 课存在但索引的「课程」块里没登记它 → 报(课躺在文件夹里,目录页看不出来)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        _mk(root, INDEX, BLOCK.replace("- 第 1 节:[0001 · 测试夹具 · 名词解释](<lessons/0001-测试夹具.html>)\n", ""))
        got = T.check_glossary_lessons()
        assert len(got) == 1 and "未在容器的「## 课程」块登记" in got[0].detail, got


def test_block_inside_code_fence_is_not_registration():
    """索引里只有一段代码示例写 `## 课程` 与文件名 → 不算登记(否则抄段示例就能过)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        _mk(root, INDEX, BLOCK.replace(
            "- 第 1 节:[0001 · 测试夹具 · 名词解释](<lessons/0001-测试夹具.html>)\n",
            "```markdown\n- 第 1 节:[0001 · 测试夹具 · 名词解释](<lessons/0001-测试夹具.html>)\n```\n"))
        got = T.check_glossary_lessons()
        assert len(got) == 1 and "未在容器的「## 课程」块登记" in got[0].detail, got


def test_missing_container_index_is_not_reported():
    """容器缺 `00-索引.md` → 登记那一半不报(索引缺失本身归 A4),免得一因两报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        (root / INDEX).unlink()
        assert not T.check_glossary_lessons(), T.check_glossary_lessons()


def test_missing_index_still_reports_missing_lesson():
    """索引缺失时只能免掉「登记」那一半:真的没开课仍然要报(否则缺索引就能藏住缺课)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        (root / INDEX).unlink()
        (root / LESSON).unlink()
        got = T.check_glossary_lessons()
        assert len(got) == 1 and "没有对应课程" in got[0].detail, got


def test_other_container_is_out_of_scope():
    """`!系统与工具` 目前不是教学工作区(没有 `lessons/`),故意不纳入管辖。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!系统与工具/20-知识/cmder.md", "---\ntype: system\nstatus: done\n---\n# cmder\n")
        _mk(root, "10-项目/!系统与工具/00-索引.md", "# !系统与工具\n")
        assert not T.check_glossary_lessons(), T.check_glossary_lessons()


def test_core_matching_accepts_longer_lesson_name():
    """课件主干比词条主干长也算一对(`巡检器` ↔ `0002-巡检器怎么用`)——两个方向都认。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!名词解释/20-知识/巡检器.md", "---\ntype: concept\nstatus: done\n---\n# 巡检器\n")
        _mk(root, "10-项目/!名词解释/lessons/0002-巡检器怎么用.html", "<title>x</title>\n")
        _mk(root, "10-项目/!名词解释/00-索引.md",
            "# 索引\n\n## 课程\n\n- 第 1 节:[x](<lessons/0002-巡检器怎么用.html>)\n")
        assert not T.check_glossary_lessons(), T.check_glossary_lessons()


def test_workspace_check_includes_glossary_rule():
    """守则必须真的挂在 `check_teach_workspace()` 上 —— 只写函数不接线是最容易犯的错。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        (root / LESSON).unlink()
        got = T.check_teach_workspace()
        assert [f.path for f in got] == [NOTE], got


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for fn in fns:
        try:
            fn()
            print("PASS", fn.__name__)
            ok += 1
        except AssertionError as e:
            print("FAIL", fn.__name__, e)
    print("PASS=%d FAIL=%d" % (ok, len(fns) - ok))
    raise SystemExit(0 if ok == len(fns) else 1)
