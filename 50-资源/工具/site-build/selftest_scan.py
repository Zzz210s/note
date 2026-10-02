#!/usr/bin/env python3
"""site_scan.py 自检:在真库上核对条目数与字段。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note/50-资源/工具/site-build && python -B selftest_scan.py

口径:条目数必须与**实时** `git ls-files` 一致(把两数各算一遍,漏收/重收都会失败)。
设计文档基线写的是 276(216 md + 60 html);2026-10-02 的记录篇入库后多 1 篇,
所以这里与实时计数对齐,而不是写死 276。
"""
from __future__ import annotations

import random
import subprocess
import sys
from pathlib import Path

import site_scan as S
import site_scan_lib as L

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = S.VAULT_ROOT
ALGO = "10-项目/!一天一道算法题/20-知识/两数之和.md"
ROOT_INDEX = "00-索引/00-索引.md"
DESIGN_BASELINE = 276


def _live_counts() -> dict:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8", errors="replace").stdout.splitlines()
    md = [p for p in out if p.endswith(".md")]
    html = [p for p in out if p.endswith(".html")]
    return {"md": len(md), "html": len(html),
            "lessons": len([p for p in html if "/lessons/" in p]),
            "know": len([p for p in md if "/20-知识/" in p])}


def _by_path(path: str) -> dict:
    for e in S.scan("all"):
        if e["path"] == path:
            return e
    raise AssertionError("找不到条目:" + path)


def test_public_counts():
    """对外集合口径:课 ∪ `20-知识/*.md`,且两数与实时 `git ls-files` 一致(不写死数字)。"""
    live = _live_counts()
    pub = S.scan("public")
    assert len(pub) == live["lessons"] + live["know"], (len(pub), live)
    assert sum(e["kind"] == "lesson" for e in pub) == live["lessons"], live
    assert sum(e["kind"] == "note" and "/20-知识/" in e["path"] for e in pub) == live["know"], live
    assert not any(e["kind"] in ("index", "scaffold") for e in pub), "public 不得含 index/scaffold"


def test_all_counts():
    live = _live_counts()
    alls = S.scan("all")
    expected = live["md"] + live["html"]
    note = "" if expected == DESIGN_BASELINE else "(设计基线 %d,已被新增记录篇 +%d)" % (
        DESIGN_BASELINE, expected - DESIGN_BASELINE)
    print("  全库 %d = %d md + %d html %s" % (expected, live["md"], live["html"], note))
    assert len(alls) == expected, (len(alls), expected)


def test_random_entries_fields():
    alls = S.scan("all")
    slugs = [e["slug"] for e in alls]
    assert len(slugs) == len(set(slugs)), "slug 必须全库唯一"
    random.seed(20261002)
    for e in random.sample(alls, 5):
        assert e["title"], e
        assert e["slug"], e
        assert e["section"], e


def test_no_empty_key_fields():
    """关键字段在任何模式下都不该是空串(空 = 解析漏了)。"""
    for e in S.scan("all"):
        for key in ("kind", "path", "title", "slug", "section", "type", "summary"):
            assert e[key], (e["path"], key)
        if not e["path"].endswith(".html"):
            assert e["body"], (e["path"], "body")
        else:
            assert e["body"] is None, (e["path"], "课不该带正文")


def test_algo_note():
    e = _by_path(ALGO)
    assert e["kind"] == "note", e["kind"]
    assert e["type"] == "algorithm", e["type"]
    assert e["status"] == "learning", e["status"]
    assert e["date"] == "2026-08-30", e["date"]
    assert "哈希表" in e["tags"], e["tags"]
    assert e["summary"], "摘要不该为空"


def test_root_index_fallback():
    e = _by_path(ROOT_INDEX)
    assert e["kind"] == "index", e["kind"]
    assert e["type"] == "索引", e["type"]
    assert e["section"], e["section"]


def test_frontmatter_related_and_tags():
    fm, body = S.parse_frontmatter(
        '---\nrelated: "[[a|b]] / [[c]]"\ntags: [x, y]\n---\n# T\n正文\n')
    assert fm["related"] == ["b", "c"], fm["related"]
    assert fm["tags"] == ["x", "y"], fm["tags"]
    assert body.lstrip().startswith("# T"), body
    fm2, _ = S.parse_frontmatter("---\ntags:\n  - p\n  - q\n---\n正文\n")
    assert fm2["tags"] == ["p", "q"], fm2["tags"]
    assert S.parse_frontmatter("没有 frontmatter") == ({}, "没有 frontmatter")


def test_slug_and_paragraph():
    assert S.slugify("x2-0001-CLI,TUI,GUI") == "x2-0001-CLI-TUI-GUI"
    assert S.slugify("!项目说明") == "项目说明"
    md = "# 标题\n\n> 引用\n\n- 列表项\n\n第一段正文,还有 `代码`。\n\n第二段。\n"
    assert S.first_paragraph(md) == "第一段正文,还有 代码。", S.first_paragraph(md)
    # 兜底路径要剥行首块级标记(`>` / `- ` / `1. `),并去掉裸 HTML 标签
    assert S.first_content("# T\n\n> 引用一句话\n") == "引用一句话", S.first_content("# T\n\n> 引用一句话\n")
    assert S.first_content("# T\n\n- 名词分为阳性\n") == "名词分为阳性"
    assert S.first_content("# T\n\n1. 加信息\n") == "加信息"
    assert L.clean_inline("前往 A<sub>注:在sudo模式下</sub>") == "前往 A 注:在sudo模式下"


def test_page_title():
    """课号(0011)与末段工作区(名词解释)都去掉;两段的参考页整段保留。"""
    assert S._page_title("0011 · tmux · 名词解释") == "tmux"
    assert S._page_title("0002 · 编辑器 / 编译器 / 解释器 / IDE · 名词解释") == "编辑器 / 编译器 / 解释器 / IDE"
    assert S._page_title("课程地图 · Docker(容器化)") == "课程地图 · Docker(容器化)"


def test_win_text():
    """.win` 抠出的必须是纯文本(无标签残留、空白已压)。"""
    e = _by_path("10-项目/!名词解释/lessons/x1-0011-tmux.html")
    assert e["kind"] == "lesson", e["kind"]
    assert e["win"], "课必须有 .win"
    assert "<" not in e["win"] and ">" not in e["win"], e["win"][:60]
    assert "  " not in e["win"], e["win"][:60]


def main() -> int:
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print("FAIL", fn.__name__, "->", exc)
        else:
            print("PASS", fn.__name__)
    if failed:
        print("结论:FAIL(%d/%d)" % (failed, len(fns)))
        return 1
    print("结论:PASS(%d)" % len(fns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
