#!/usr/bin/env python3
"""A11 工作区判据与容器口径自检(2026-09-25 Task 14 修复轮 m4)。

原判据只守带 `!项目说明.md` 的学习项目,而容器(`!名词解释`)与只有 `lessons/` 的工作区
走不到那个循环 —— 它们的 MISSION / RESOURCES / NOTES 被删掉时没有任何检查会报
(三件套按协议豁免 A3/A5/A6/A7)。这里验证新判据:凡教学工作区(有 `lessons/`、或三件套
中任一份、或 `!项目说明.md`)都要求三件套齐全且非空壳,容器与学习项目同一套。
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_teach as T
import checks_lessons as S
from selftest_teach import _mk, _proj, _scaffold, MISSION_OK

INDEX = ("# !名词解释(容器)\n\n## 课程\n\n- 课程地图:暂无(尚未生成课程地图)\n")


def test_container_scaffold_missing_is_reported():
    """容器(`!名词解释`)有 lessons/ 就是工作区:三件套一个都不能少。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!名词解释/lessons/0001-测试夹具.html", "<title>x</title>\n")
        got = T.check_teach_workspace()
        assert {f.path for f in got} == {"10-项目/!名词解释"}, got
        assert {f.detail for f in got} == {
            "缺 MISSION.md(教学工作区状态层)",
            "缺 RESOURCES.md(教学工作区状态层)",
            "缺 NOTES.md(教学工作区状态层)"}, got


def test_container_scaffold_complete_passes():
    """容器三件套齐全 + 索引有「## 课程」块 → 不报(它没有 `20-知识/`,词条那一半跳过)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _scaffold(root, "!名词解释")
        _mk(root, "10-项目/!名词解释/lessons/0001-测试夹具.html", "<title>x</title>\n")
        _mk(root, "10-项目/!名词解释/00-索引.md", INDEX)
        assert not T.check_teach_workspace(), T.check_teach_workspace()


def test_deleting_one_of_three_is_reported():
    """变异证据(本次修复的动机):把容器三件套里的 NOTES.md 删掉 → 必须变红。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _scaffold(root, "!名词解释")
        _mk(root, "10-项目/!名词解释/lessons/0001-测试夹具.html", "<title>x</title>\n")
        _mk(root, "10-项目/!名词解释/00-索引.md", INDEX)
        assert not T.check_teach_workspace(), "前置:齐全时不该报"
        (root / "10-项目/!名词解释/NOTES.md").unlink()
        got = T.check_teach_workspace()
        assert len(got) == 1 and got[0].detail == "缺 NOTES.md(教学工作区状态层)", got


def test_lessons_dir_alone_makes_work_area():
    """只有 `lessons/`(既无项目说明也无三件套)也算工作区 —— 靠删文件躲不掉管辖。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/lessons/0001-x.html", "<title>x</title>\n")
        got = T.check_teach_workspace()
        assert {f.detail for f in got} == {
            "缺 MISSION.md(教学工作区状态层)",
            "缺 RESOURCES.md(教学工作区状态层)",
            "缺 NOTES.md(教学工作区状态层)"}, got


def test_notes_shell_is_reported():
    """NOTES.md 还在但被写成占位(缺 `## 教学偏好`)→ 报空壳;项目型同样受管。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _proj(root)
        _mk(root, "10-项目/甲/NOTES.md", "# NOTES\n\n待补\n")
        got = T.check_teach_workspace()
        assert len(got) == 1 and "缺章节 ## 教学偏好" in got[0].detail, got
        assert got[0].path == "10-项目/甲/NOTES.md", got


def test_tracking_dir_stays_exempt():
    """真库口径不误伤:`!问题追踪` 没有 lessons/ 也没有三件套 → 仍不管辖。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!问题追踪/EmberTimer.md", "---\ntype: log\n---\n# x\n")
        _mk(root, "10-项目/!系统与工具/20-知识/cmder.md", "---\ntype: system\n---\n# x\n")
        assert not T.check_teach_workspace(), T.check_teach_workspace()


def test_lesson_scope_is_not_hardcoded():
    """课件登记判据的作用范围:任何「有 lessons/」的目录都算,不硬编码容器名;
    只有 `reference/`(卡已退役)或只有 `20-知识/` 的目录不进这个范围。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/lessons/0001-x.html", "<title>x</title>\n")
        _mk(root, "10-项目/乙/reference/课程地图.html", "<title>地图</title>\n")
        _mk(root, "10-项目/丙/20-知识/只有知识.md", "x\n")
        names = {p.name for p in S._workspaces()}
        assert names == {"甲"}, names


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