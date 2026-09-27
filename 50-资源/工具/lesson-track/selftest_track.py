#!/usr/bin/env python3
"""按次数改名的自检(2026-09-27):前缀规则、计数归一、按课号兜底、改名不动别人的字。

真库不动:把 track_lib 的仓库根指到临时目录,造一个假项目来验。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import track_lib as T
import rename_by_count as R
import vscode_history as V


def _fake(root: Path) -> None:
    T.VAULT = root
    R.T.VAULT = root
    proj = root / "10-项目" / "甲"
    (proj / "lessons").mkdir(parents=True)
    (proj / "lessons" / "0001-测试课.html").write_text("<title>0001 · 测试课</title>", encoding="utf-8")
    (proj / "lessons" / "0002-新名.html").write_text("<title>0002 · 新名</title>", encoding="utf-8")
    (proj / "lessons" / "0003-没读过.html").write_text("<title>0003 · 没读过</title>", encoding="utf-8")
    (proj / "00-索引.md").write_text(
        "## 课程\n\n"
        "- 第 1 节:[0001 · 测试课](<lessons/0001-测试课.html>)\n"
        "- 第 2 节:[0002 · 新名](<lessons/0002-新名.html>)\n"
        "- 第 3 节:[0003 · 没读过](<lessons/0003-没读过.html>)\n"
        "- 链接别处:[另一课](<lessons/0001-测试课.html>#x)\n", encoding="utf-8")
    (proj / "lessons" / "0001-测试课.html").write_text(
        "<title>0001 · 测试课</title>\n<p>看 <a href=\"0003-没读过.html\">0003</a></p>\n", encoding="utf-8")


def test_prefix_rule():
    """① 规则:0 次不加前缀;n 次加 `x<n>-`;次数越大排得越后(`x2-` > `x10-` 除外,按自然序)。"""
    assert R.base_name("x2-0001-a.html") == "0001-a.html"
    assert R.base_name("0001-a.html") == "0001-a.html"
    assert R.target_name("0001-a.html", 0) == "0001-a.html"
    assert R.target_name("0001-a.html", 1) == "x1-0001-a.html"
    assert R.target_name("0001-a.html", 12) == "x12-0001-a.html"


def test_count_key_is_prefix_free():
    """② 计数键去前缀 —— 改名后仍然认得出来(改名前后的键必须相等)。"""
    assert T.norm_key("10-项目/甲/lessons/x3-0001-a.html") == "10-项目/甲/lessons/0001-a.html"
    assert T.norm_key("10-项目/甲/lessons/0001-a.html") == "10-项目/甲/lessons/0001-a.html"


def test_plan_matches_by_number_when_renamed():
    """③ 记录里是旧名(0002-旧名)、盘上是新名(0002-新名)→ 按课号兜底,次数仍然算上。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        T.COUNT_FILE = root / "counts.json"
        T.save({"10-项目/甲/lessons/0002-旧名.html": {"service": 0, "vscode": 4, "count": 4,
                                                      "first": "2026-09-01", "last": "2026-09-27"},
                "10-项目/甲/lessons/0001-测试课.html": {"service": 0, "vscode": 2, "count": 2,
                                                        "first": "2026-09-01", "last": "2026-09-27"}})
        plan = {f.name: n.name for f, n in R.build_plan().items()}
        assert plan.get("0001-测试课.html") == "x2-0001-测试课.html", plan
        assert plan.get("0002-新名.html") == "x4-0002-新名.html", plan
        assert "0003-没读过.html" not in plan, plan


def test_apply_renames_and_rewrites_refs():
    """④ 真改:文件改名 + 索引与课间链接一起跟着改,没读过的保持原样。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        T.COUNT_FILE = root / "counts.json"
        T.save({"10-项目/甲/lessons/0001-测试课.html": {"service": 0, "vscode": 3, "count": 3,
                                                        "first": "2026-09-01", "last": "2026-09-27"}})
        assert R.main(["--apply"]) == 0
        lessons = sorted(p.name for p in (root / "10-项目" / "甲" / "lessons").glob("*.html"))
        assert "x3-0001-测试课.html" in lessons and "0003-没读过.html" in lessons, lessons
        idx = (root / "10-项目" / "甲" / "00-索引.md").read_text(encoding="utf-8")
        assert "x3-0001-测试课.html" in idx and "x3-0001-测试课.html>#x" in idx, idx
        assert "0003-没读过.html" in idx, idx
        assert not (root / "10-项目" / "甲" / "lessons" / "0001-测试课.html").exists()


def test_repeat_run_is_stable():
    """⑤ 再跑一次(次数没变)不该再改名 —— 否则每次都要动文件。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        T.COUNT_FILE = root / "counts.json"
        T.save({"10-项目/甲/lessons/0001-测试课.html": {"service": 0, "vscode": 3, "count": 3,
                                                        "first": "2026-09-01", "last": "2026-09-27"}})
        R.main(["--apply"])
        assert R.build_plan() == {}, R.build_plan()


def test_url_parsing_still_works():
    """⑥ URL 解析:file:// 与本地服务两种写法都要能对上;非课件返回 None。"""
    V.VAULT = Path(r"F:/0-Note")
    got = V._rel_from_url("file:///f%3A/0-Note/10-%E9%A1%B9%E7%9B%AE/%21%E5%90%8D%E8%AF%8D%E8%A7%A3%E9%87%8A/lessons/0001-CLI%2CTUI%2CGUI.html")
    assert got == "10-项目/!名词解释/lessons/0001-CLI,TUI,GUI.html", got
    assert V._rel_from_url("https://example.com/x.html") is None


def test_real_vault_has_no_stray_prefix():
    """⑦ 真库:课件名里除了规范的 `x<数字>-` 前缀,不该出现别的前缀写法。"""
    import re
    base = Path(__file__).resolve().parents[3] / "10-项目"
    bad = [p.name for p in list(base.glob("*/lessons/*.html")) + list(base.glob("*/reference/*.html"))
           if re.match(r"^x(?!\d+-)", p.name)]
    assert not bad, bad[:5]


def test_rewrite_does_not_stack_prefixes():
    """⑧ 已带前缀的文件名不会被再叠一层(`x1-0003-a.html` 里的 `0003-a.html` 不能再被替换)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        T.COUNT_FILE = root / "counts.json"
        T.save({"10-项目/甲/lessons/0001-测试课.html": {"service": 0, "vscode": 3, "count": 3,
                                                        "first": "2026-09-01", "last": "2026-09-27"}})
        R.main(["--apply"])          # 第一次:0001 → x3-0001
        R.main(["--apply"])          # 第二次:不该再叠
        idx = (root / "10-项目" / "甲" / "00-索引.md").read_text(encoding="utf-8")
        assert "x3-x3-" not in idx, idx
        assert idx.count("x3-0001-测试课.html") == 2, idx   # 课程行 + 那个带锚点的例子


def test_close_counting_and_max():
    """⑨ 关闭上报是主口径:closed 计数进 count,且与另两个来源取最大值。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _fake(root)
        T.COUNT_FILE = root / "counts.json"
        T.save({})
        rel = "10-项目/甲/lessons/0001-测试课.html"
        rec = T.bump_close(rel)
        assert rec["closed"] == 1 and rec["count"] == 1, rec
        rec = T.bump_close(rel)
        assert rec["closed"] == 2 and rec["count"] == 2, rec
        data = T.load()
        data[rel]["vscode"] = 5
        data[rel] = T._recount(data[rel]); T.save(data)
        assert T.load()[rel]["count"] == 5, T.load()[rel]


def test_closed_enough_rule():
    """⑩ "可以算读完"的判据:上报过关闭就直接算;否则要历史里最后一次出现超过宽限期。"""
    import time as _t
    import watch as W
    assert W._closed_enough({"closed": 1}) is True
    assert W._closed_enough({"closed": 0, "hist_last_ms": int(_t.time() * 1000)}) is False
    assert W._closed_enough({"closed": 0,
                             "hist_last_ms": int(_t.time() * 1000) - W.CLOSE_GRACE_MS - 1000}) is True
    assert W._closed_enough({}) is False


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
