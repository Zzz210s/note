#!/usr/bin/env python3
"""计数与回写的自检(2026-09-27):两个来源取最大值、按课号兜底、重复跑幂等。

真库不动:把 track_lib 的仓库根与计数文件都指到临时目录,造一个假项目来验。
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import track_lib as T


def _setup(root: Path, counts: dict) -> None:
    T.VAULT = root
    T.COUNT_FILE = root / "counts.json"
    proj = root / "10-项目" / "甲"
    (proj / "lessons").mkdir(parents=True)
    (proj / "lessons" / "0001-测试课.html").write_text("<title>0001 · 测试课</title>", encoding="utf-8")
    (proj / "lessons" / "0002-旧名.html").write_text("<title>0002 · 新名</title>", encoding="utf-8")
    (proj / "00-索引.md").write_text(
        "## 课程\n\n"
        "- 第 1 节:[0001 · 测试课](<lessons/0001-测试课.html>)\n"
        "- 第 2 节:[0002 · 新名](<lessons/0002-旧名.html>)\n", encoding="utf-8")
    T.save(counts)


def _index(root: Path) -> str:
    return (root / "10-项目" / "甲" / "00-索引.md").read_text(encoding="utf-8")


def test_max_of_two_sources_not_sum():
    """① 服务计 3 次、历史 5 次 → 写 5 次(取最大值,不是 8)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _setup(root, {"10-项目/甲/lessons/0001-测试课.html": {"service": 3, "vscode": 5, "count": 5,
                                                              "first": "2026-09-01", "last": "2026-09-27"}})
        T.write_index_suffixes()
        line = [l for l in _index(root).splitlines() if "0001-" in l][0]
        assert "进入 5 次" in line, line


def test_renamed_lesson_falls_back_to_number():
    """② 历史里是旧文件名(0002-旧名),索引里也叫旧名 → 照样对得上并写次数。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _setup(root, {"10-项目/甲/lessons/0002-旧名.html": {"service": 0, "vscode": 4, "count": 4,
                                                            "first": "2026-09-01", "last": "2026-09-27"}})
        T.write_index_suffixes()
        line = [l for l in _index(root).splitlines() if "0002-" in l][0]
        assert "进入 4 次" in line, line


def test_repeat_run_is_idempotent():
    """③ 连跑三次,行尾标记不叠加(先剥旧后缀再写新的)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _setup(root, {"10-项目/甲/lessons/0001-测试课.html": {"service": 0, "vscode": 2, "count": 2,
                                                              "first": "2026-09-01", "last": "2026-09-27"}})
        for _ in range(3):
            T.write_index_suffixes()
        line = [l for l in _index(root).splitlines() if "0001-" in l][0]
        assert line.count("进入") == 1 and "进入 2 次" in line, line


def test_bump_only_touches_service_counter():
    """④ 服务 +1 只动 service 计数,count 取两者较大者。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _setup(root, {"10-项目/甲/lessons/0001-测试课.html": {"service": 0, "vscode": 5, "count": 5,
                                                              "first": "2026-09-01", "last": "2026-09-01"}})
        rec = T.bump("10-项目/甲/lessons/0001-测试课.html")
        assert rec["service"] == 1 and rec["vscode"] == 5 and rec["count"] == 5, rec
        rec = T.bump("10-项目/甲/lessons/0001-测试课.html")
        assert rec["service"] == 2 and rec["count"] == 5, rec
        for _ in range(5):
            rec = T.bump("10-项目/甲/lessons/0001-测试课.html")
        assert rec["count"] == 7, rec


def test_add_url_to_rel_and_back():
    """⑤ URL 解析:file:// 与本地服务两种写法都要能对上;非课件返回 None。"""
    import vscode_history as V
    V.VAULT = Path(r"F:/0-Note")
    got = V._rel_from_url("file:///f%3A/0-Note/10-%E9%A1%B9%E7%9B%AE/%21%E5%90%8D%E8%AF%8D%E8%A7%A3%E9%87%8A/lessons/0001-CLI%2CTUI%2CGUI.html")
    assert got == "10-项目/!名词解释/lessons/0001-CLI,TUI,GUI.html", got
    got2 = V._rel_from_url("http://127.0.0.1:8787/10-项目/甲/lessons/0001-测试课.html")
    assert got2 == "10-项目/甲/lessons/0001-测试课.html", got2
    assert V._rel_from_url("file:///f%3A/0-Note/README.md") is None
    assert V._rel_from_url("https://example.com/x.html") is None


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
