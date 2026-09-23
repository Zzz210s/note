#!/usr/bin/env python3
"""check_vault 自检:在临时目录里造假库,验证各检查项能抓到问题。"""
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
        _mk(root, "00-MOC/x.md", "---\ntype: note\nstatus: done\n---\n- [A](<../20-Areas/a.md>)\n")
        _mk(root, "20-Areas/a.md", "---\ntype: note\nstatus: done\n---\n[断](<../nowhere.md>)\n")
        _mk(root, "20-Areas/orphan.md", "---\ntype: knowledge\nstatus: 进行中\n---\n正文\n")
        assert len(C.check_links()) == 1, C.check_links()
        assert {f.path for f in C.check_orphans()} == {"20-Areas/orphan.md"}
        meta = C.check_meta()
        assert any("type" in f.detail for f in meta) and any("status" in f.detail for f in meta), meta
        assert not C.check_wikilinks()

def test_wikilink_path_form_resolves():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-Projects/p/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-Projects/p/n.md", '---\ntype: note\nstatus: done\nrelated: "[[p/!项目说明|项目说明]]"\n---\nx\n')
        assert not C.check_wikilinks(), C.check_wikilinks()

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
