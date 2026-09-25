#!/usr/bin/env python3
"""A14(索引页一致性)自检之一:根索引的项目清单(判据①)与入口提示通道。

真库此刻既没有根索引、也没有任何 `20-知识/`,空跑证明不了新代码路径,故夹具自带。
判据②(项目索引的知识链接数)与 A4/A9 分工的用例在 `selftest_index2.py`(守 ≤200 行)。
"""
import contextlib
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_index as I
import checks_project as P
import check_vault as C


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _project(root: Path, name: str) -> None:
    """一个带 `20-知识/` 的项目(说明 + 一篇知识笔记);项目索引页由用例自己写。"""
    _mk(root, "10-项目/%s/!项目说明.md" % name,
        "---\ntype: project\nstatus: learning\n---\n\n# %s\n" % name)
    _mk(root, "10-项目/%s/20-知识/知识1.md" % name,
        "---\ntype: note\nstatus: learning\nrelated: \"[[%s/!项目说明|项目]]\"\n---\n\n# 知识1\n"
        % name)


def test_root_index_reports_missing_project():
    """根索引只列了项目、漏了容器 → 报 A14,且报的是那条缺失项本身。

    容器是 A7 够不到的地方(`project_dirs()` 只认带 `!项目说明.md` 的目录),所以这条
    清单检查不是 A7 的复述。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        (root / "10-项目/!名词解释").mkdir(parents=True)
        _mk(root, "00-索引.md", "---\ntype: note\nstatus: done\n---\n\n# 索引\n\n"
            "- [甲](<10-项目/甲/!项目说明.md>)\n")
        got = I.check_root_lists_projects()
        assert [(f.path, f.line, f.detail) for f in got] == [
            ("00-索引.md", 0, "根索引未列出项目 !名词解释")], got
        assert not [f for f in P.check_roadmap() if "名词解释" in f.detail], P.check_roadmap()
        assert I.check_project_index_links() == [], I.check_project_index_links()


def test_root_index_lists_all_is_green():
    """项目与容器都各占一行 → 0 处(表格行同样算,不挑写法)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        (root / "10-项目/!名词解释").mkdir(parents=True)
        _mk(root, "00-索引.md", "---\ntype: note\nstatus: done\n---\n\n# 索引\n\n"
            "| 项目 | 状态 |\n| --- | --- |\n| [甲](<10-项目/甲/00-索引.md>) | learning |\n"
            "| [名词解释](<10-项目/!名词解释/00-索引.md>) | — |\n")
        assert I.check_root_lists_projects() == [], I.check_root_lists_projects()


def test_missing_root_index_skips_check():
    """根索引不存在 → ①整条跳过(过渡期不误报),只留提示;提示不进 check_* 的返回值。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        (root / "10-项目/!名词解释").mkdir(parents=True)
        assert I.check_index_consistency() == [], I.check_index_consistency()
        hints = I.index_hints()
        assert len(hints) == 2 and "2 个项目目录" in hints[0], hints
        assert len(I.index_hints(verbose=False)) == 1, I.index_hints(verbose=False)


def test_no_project_dir_no_hint():
    """`10-项目/` 下没有目录(或整个不存在)→ 连提示都不给。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        assert I.project_subdirs() == [] and I.index_hints() == [], I.index_hints()


def test_hint_channel_keeps_entry_point_passing():
    """入口链路:根索引缺失的提示打印了,`[A14 …] 0 处` 与 rc=0 都不受影响(A12 同款守门)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        (root / "10-项目/!名词解释").mkdir(parents=True)   # 只有容器、没有项目 → A7 提前返回,库仍全绿
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = C.main(["--quiet"])
        text = buf.getvalue()
        assert "[提示] 根 00-索引.md 未创建" in text, text
        assert "[A14 索引页一致性] 0 处" in text, text
        assert "结论:PASS" in text and rc == 0, (rc, text)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
