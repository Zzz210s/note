#!/usr/bin/env python3
"""vault_lib 自检:纯断言,无第三方依赖。运行:python selftest_lib.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

def test_parse_frontmatter():
    fm = L.parse_frontmatter("---\ntype: note\ntags: [a, b]\n---\n正文")
    assert fm is not None and fm["type"] == "note", fm
    assert L.parse_frontmatter("无 frontmatter") is None

def test_extract_links_skips_code():
    text = "行内 `[文字](网址)` 不算\n\n```\n[也](不算)\n```\n\n真链接 [a](<../b.md>)\n"
    got = [t for _, t in L.extract_links(text)]
    assert got == ["../b.md"], got

def test_extract_links_line_numbers():
    got = list(L.extract_links("第一行\n第二行 [x](<y.md>)\n"))
    assert got == [(2, "y.md")], got

def test_extract_wikilinks():
    got = [t for _, t in L.extract_wikilinks("见 [[冒泡算法]] 与 [[a/b|别名]]")]
    assert got == ["冒泡算法", "a/b|别名"], got

def test_md_stems_nonempty():
    stems = L.md_stems()
    assert "冒泡算法" in stems and len(stems) > 100, len(stems)

def test_md_stem_counts_flags_duplicates():
    counts = L.md_stem_counts()
    assert counts.get("!项目说明", 0) > 1, counts.get("!项目说明")
    assert counts.get("冒泡算法") == 1, counts.get("冒泡算法")
    assert len(counts) == len(L.md_stems()), (len(counts), len(L.md_stems()))

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
