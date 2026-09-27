#!/usr/bin/env python3
"""teach-links.py 自检:正文级联动判据、页头/页脚不计入、对称性、退出码。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note && python -B 50-资源/工具/selftest_teach_links.py

判据都跑在**假库**(临时目录里几节假课)上,不碰真课程目录;
只有最后一条 `test_keywords_cover_real_lessons` 读真目录,它守的是"新增课必须登记关键词"。
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "teach-links.py"
LESSONS = Path(__file__).resolve().parents[2] / "10-项目" / "!名词解释" / "lessons"


def _load_tool():
    spec = importlib.util.spec_from_file_location("teach_links", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load_tool()
PREFIX_RE = M.PREFIX_RE   # 课件名可能带 `x<次数>-` 前缀(按阅读次数改名)

TMPL = """<!doctype html>
<html lang="zh-CN"><head><title>{title}</title></head><body>
{meta}
<h2>1 | 定义</h2>
<p>{body}</p>
{footer}
</body></html>
"""
A, B, C = "0001-CLI,TUI,GUI.html", "0011-tmux.html", "0012-GRUB.html"


def _write(root: Path, name: str, meta: str, body: str, footer: str = "") -> None:
    (root / name).write_text(TMPL.format(title=name, meta=meta, body=body, footer=footer),
                             encoding="utf-8")


def _vault(files: dict[str, tuple[str, str, str]]):
    """files: 文件名 -> (meta, body, footer);返回临时目录(调用方负责清理)。"""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for name, (meta, body, footer) in files.items():
        _write(root, name, meta, body, footer)
    return tmp, root


def _scan(root: Path):
    return M.scan(M.load(root))


def test_body_keyword_without_link_is_pending():
    tmp, root = _vault({B: ("", "程序住在 tmux 服务端里,终端模拟器只是看一眼的窗口。", ""),
                        A: ("", "三种界面形态。", "")})
    rows = _scan(root)
    assert [(r["stem"], r["target"]) for r in rows] == [("0011-tmux", "0001-CLI,TUI,GUI")], rows
    assert rows[0]["kws"] == [("终端模拟器", 1)], rows[0]


def test_body_link_satisfies_rule():
    tmp, root = _vault({B: ("", '它住在 <a href="0001-CLI,TUI,GUI.html">终端模拟器</a> 里。', ""),
                        A: ("", "三种界面形态。", "")})
    assert _scan(root) == []


def test_meta_and_footer_links_do_not_count():
    meta = '<p class="lesson-meta">课程 0011 · 前置:<a href="0001-CLI,TUI,GUI.html">0001</a></p>'
    footer = '<footer><p>相关课:<a href="0001-CLI,TUI,GUI.html">0001</a></p></footer>'
    tmp, root = _vault({B: (meta, "终端模拟器只是看一眼的窗口。", footer), A: ("", "三种界面。", "")})
    assert [r["target"] for r in _scan(root)] == ["0001-CLI,TUI,GUI"]


def test_both_directions_are_reported():
    tmp, root = _vault({B: ("", "终端模拟器只是看一眼的窗口。", ""),
                        A: ("", "想让断线后的事继续跑,得靠终端复用器。", "")})
    got = {(r["stem"], r["target"]) for r in _scan(root)}
    assert got == {("0011-tmux", "0001-CLI,TUI,GUI"), ("0001-CLI,TUI,GUI", "0011-tmux")}, got


def test_one_way_body_edge_is_reported():
    tmp, root = _vault({A: ("", '关掉窗口还在跑,那是 <a href="0011-tmux.html">0011</a> 那一层。', ""),
                        B: ("", "tmux 是一个终端复用器。", "")})
    assert M.one_way(M.edge_map(M.load(root))) == [("0001-CLI,TUI,GUI", "0011-tmux")]


def test_one_way_ignores_header_only_edge():
    meta = '<p class="lesson-meta">课程 0001 · 前置:<a href="0011-tmux.html">0011</a></p>'
    tmp, root = _vault({A: (meta, "三种界面形态。", ""), B: ("", "tmux 是一个终端复用器。", "")})
    assert M.one_way(M.edge_map(M.load(root))) == []


def test_ascii_keyword_respects_word_boundary():
    tmp, root = _vault({"0007-UI与UX.html": ("", "build 一个 GUI 界面,别把 ui 当词根。", ""),
                        A: ("", "三种界面形态。", "")})
    targets = [r["target"] for r in _scan(root)]
    assert "0007-UI与UX" not in targets, "build / GUI 里的 ui 不该命中 UI"
    assert "0001-CLI,TUI,GUI" in targets, "大写 GUI 本身应该命中"


def test_cjk_keyword_matches_substring():
    tmp, root = _vault({"0002-编辑器,编译器,解释器,IDE.html": ("", "编辑器与编译器都在这条链上。", ""),
                        A: ("", "这个解释器的活是听话照做。", "")})
    assert [r["target"] for r in _scan(root)] == ["0002-编辑器,编译器,解释器,IDE"]


def test_exit_code_tracks_pending_and_one_way():
    tmp, root = _vault({B: ("", "终端模拟器只是看一眼的窗口。", ""), A: ("", "三种界面形态。", "")})
    argv = sys.argv
    try:
        sys.argv = ["teach-links.py", "--dir", str(root), "--quiet"]
        def rc():
            with redirect_stdout(io.StringIO()):
                return M.main()
        assert rc() == 1, "--quiet 有待办时应返回 1"
        _write(root, B, "", '它住在 <a href="0001-CLI,TUI,GUI.html">终端模拟器</a> 里。')
        assert rc() == 1, "只链单向时仍应返回 1(单向联动)"
        _write(root, A, "", '长期托管是 <a href="0011-tmux.html">0011</a> 那一层。')
        assert rc() == 0, "两向都链上后应返回 0"
    finally:
        sys.argv = argv


def test_keywords_cover_real_lessons():
    real = {PREFIX_RE.sub("", p.stem) for p in LESSONS.glob("*.html")}
    assert real == set(M.KEYWORDS), (real ^ set(M.KEYWORDS))


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
