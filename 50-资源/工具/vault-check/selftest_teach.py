#!/usr/bin/env python3
"""A11(教学工作区)自检:该报的报、不该报的不报。"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_teach as T

MISSION_OK = ("# Mission: 测试\n\n## Why\n\n因为。\n\n## Success looks like\n\n- 会做\n\n"
              "## Constraints\n\n- 无\n\n## Out of scope\n\n- 无\n")
RES_OK = "# 测试 Resources\n\n## Knowledge\n\n- [官方](https://example.com)\n  用在:一切\n\n## Gaps\n\n- 无\n"


def _mk(root: Path, rel: str, body: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_missing_scaffold_is_reported():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\n---\nx\n")
        _mk(root, "10-项目/甲/MISSION.md", MISSION_OK)
        got = T.check_teach_workspace()
        assert len(got) == 1 and "RESOURCES.md" in got[0].detail, got


def test_complete_workspace_passes():
    """状态层齐全即过。注意本用例没建 `00-索引.md` —— 项目索引缺失归 A4,A11 不重复报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\n---\nx\n")
        _mk(root, "10-项目/甲/MISSION.md", MISSION_OK)
        _mk(root, "10-项目/甲/RESOURCES.md", RES_OK)
        assert not T.check_teach_workspace(), T.check_teach_workspace()


def test_empty_shell_is_reported():
    """文件在、内容是占位 —— 也要报,否则半年后会留下一堆空壳。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\n---\nx\n")
        _mk(root, "10-项目/甲/MISSION.md", "# Mission: 测试\n\nTODO\n")
        _mk(root, "10-项目/甲/RESOURCES.md", RES_OK)
        got = T.check_teach_workspace()
        assert len(got) == 1 and "缺章节" in got[0].detail, got


def test_missing_course_block_is_reported():
    """课躺在 lessons/ 里、目录页没登记 —— A11 必须报(否则等于没适配)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\n---\nx\n")
        _mk(root, "10-项目/甲/MISSION.md", MISSION_OK)
        _mk(root, "10-项目/甲/RESOURCES.md", RES_OK)
        _mk(root, "10-项目/甲/00-索引.md", "---\ntype: note\nstatus: learning\n---\n\n# 甲\n")
        got = T.check_teach_workspace()
        assert len(got) == 1 and "课程" in got[0].detail, got


def test_course_block_registered_passes():
    """索引页带「## 课程」块就不报(块里的条目数 / 文件名不归 A11 管)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\n---\nx\n")
        _mk(root, "10-项目/甲/MISSION.md", MISSION_OK)
        _mk(root, "10-项目/甲/RESOURCES.md", RES_OK)
        _mk(root, "10-项目/甲/00-索引.md",
            "---\ntype: note\nstatus: learning\n---\n\n# 甲\n\n## 课程\n\n- 课程地图:暂无\n")
        assert not T.check_teach_workspace(), T.check_teach_workspace()


def test_non_learning_dir_is_exempt():
    """没有 `!项目说明.md` 的目录(如追踪区)不在管辖范围。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!问题追踪/a.md", "# 追踪\n")
        assert not T.check_teach_workspace(), T.check_teach_workspace()


def test_scaffold_detection_scope():
    """is_teach_scaffold 只认 10-项目 下的教学工作区。"""
    assert L.is_teach_scaffold("10-项目/甲/MISSION.md")
    assert L.is_teach_scaffold("10-项目/甲/lessons/0001-x.html")
    assert L.is_teach_scaffold("10-项目/甲/learning-records/0001-y.md")
    assert not L.is_teach_scaffold("10-项目/甲/!项目说明.md")
    assert not L.is_teach_scaffold("20-领域/10-名词解释/巡检器.md")
    assert not L.is_teach_scaffold("50-资源/工具/MISSION.md")


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
