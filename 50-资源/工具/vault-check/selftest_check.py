#!/usr/bin/env python3
"""A1~A6 自检:在临时目录里造假库,验证断链/双链/孤篇/元数据能抓到问题。

A4 的用例在 `selftest_a4.py`;A7~A10(路线/标签/知识归属)在 `selftest_extra.py`
与 `selftest_project*.py` —— 按主题拆文件只为一件事:每个自研文件守住 ≤200 行。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import check_vault as C

def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p

def test_detects_broken_link_and_orphan_and_meta():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引.md", "---\ntype: note\nstatus: done\n---\n- [A](<20-领域/a.md>)\n")
        _mk(root, "20-领域/a.md", "---\ntype: note\nstatus: done\n---\n[断](<../nowhere.md>)\n")
        _mk(root, "20-领域/orphan.md", "---\ntype: knowledge\nstatus: 进行中\n---\n正文\n")
        assert len(C.check_links()) == 1, C.check_links()
        assert {f.path for f in C.check_orphans()} == {"20-领域/orphan.md"}
        meta = C.check_meta()
        assert any("type" in f.detail for f in meta) and any("status" in f.detail for f in meta), meta
        assert not C.check_wikilinks()

def test_wikilink_path_form_resolves():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/p/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/p/n.md", '---\ntype: note\nstatus: done\nrelated: "[[p/!项目说明|项目说明]]"\n---\nx\n')
        assert not C.check_wikilinks(), C.check_wikilinks()

def test_a3_bare_wikilink_needs_unique_stem():
    """裸双链 [[名]] 在同名文件不唯一时不计数(否则一处裸链给所有同名文件发入链)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引.md", "---\ntype: note\nstatus: done\n---\n[[!项目说明]] [[冒泡算法]]\n")
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/乙/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "20-领域/冒泡算法.md", "---\ntype: algorithm\nstatus: done\n---\nx\n")
        got = {f.path for f in C.check_orphans()}
        assert "10-项目/甲/!项目说明.md" in got and "10-项目/乙/!项目说明.md" in got, got
        assert "20-领域/冒泡算法.md" not in got, got

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
