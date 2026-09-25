#!/usr/bin/env python3
"""A13 自检(反向来源):缺来源 / 合格写法 / 首段口径 / 缺索引归 A4 / 空知识目录。

夹具是最小的 `10-项目/<项目>/` 三件套(`!项目说明.md` + `00-索引.md` + `20-知识/x.md`),
所以本文件只测 A13 自己的反向判据;容器与非项目目录的豁免、入口退出码在 selftest_backlink2.py,
缺索引的归因(属 A4)在这里断言。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_backlink as B
import check_vault as C

SPEC = "---\ntype: project\nstatus: learning\n---\n\n# %s\n"
INDEX = """---
type: note
status: learning
---

# %s 索引

> 本项目知识 1 篇 · 状态 learning · 覆盖 1/1(100%%)

## 知识产出

- [x](<./20-知识/x.md>)
"""
NOTE = "---\ntype: note\nstatus: learning\n%s---\n\n# x\n\n%s\n"
RELATED = 'related: "[[甲/!项目说明|项目]]"\n'


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _project(root: Path, fm: str = "", body: str = "正文,不提来源。",
             index: bool = True, note: bool = True) -> None:
    """一个项目的最小三件套;note=False 时不写知识笔记。"""
    _mk(root, "10-项目/甲/!项目说明.md", SPEC % "甲")
    if index:
        _mk(root, "10-项目/甲/00-索引.md", INDEX % "甲")
    if note:
        _mk(root, "10-项目/甲/20-知识/x.md", NOTE % (fm, body))


def test_a13_missing_backlink_reported():
    """A13 Step 1 用例:知识笔记没写来源项目(项目索引里却列了它)→ 报 A13。"""
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT)
        got = B.check_project_backlinks()
        assert len(got) == 1, got
        assert (got[0].stage, got[0].path) == ("A13", "10-项目/甲/20-知识/x.md"), got


def test_related_wikilink_without_md_satisfies():
    """不带 `.md`:frontmatter 写 `related: "[[甲/!项目说明|项目]]"` 即算写明来源(Obsidian 惯例)。"""
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT, fm=RELATED)
        assert B.check_project_backlinks() == [], B.check_project_backlinks()


def test_related_wikilink_with_md_satisfies():
    """带 `.md`:简报规定的写法 `related: "[[甲/!项目说明.md|项目]]"` 也满足(比 stem 前先去后缀)。

    变异证据:把 `_points_to_spec` 的 `stem = core[:-3] if core.endswith(".md") else core`
    改成 `stem = core`(关掉去后缀分支)→ 裸名对不上 `!项目说明`、后缀也对不上无后缀的 tail:
    本用例与两条带 `.md` 的 markdown 链接用例一同变红(实测 3 红)。
    """
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT, fm='related: "[[甲/!项目说明.md|项目]]"\n')
        assert B.check_project_backlinks() == [], B.check_project_backlinks()


def test_related_vault_path_wikilink_satisfies():
    """库根相对写法 `[[10-项目/甲/!项目说明|甲]]` 也认(路径后缀口径与 A2 一致)。"""
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT, fm='related: "[[10-项目/甲/!项目说明|甲]]"\n')
        assert B.check_project_backlinks() == [], B.check_project_backlinks()


def test_related_markdown_link_satisfies():
    """markdown 链接按笔记所在目录解析:`[项目](../!项目说明.md)` 也算。"""
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT, fm='related: "[项目](../!项目说明.md)"\n')
        assert B.check_project_backlinks() == [], B.check_project_backlinks()


def test_nested_note_resolves_spec_from_project_root():
    """`20-知识/子目录/x.md` 的相对链接按**项目根**解析,不按 `20-知识/` 解析(不误报)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, fm=RELATED)
        nested = _mk(root, "10-项目/甲/20-知识/子目录/z.md",
                     NOTE % ('related: "[项目](../../!项目说明.md)"\n', "正文。"))
        assert (nested.parent / "../../!项目说明.md").resolve().is_file()
        assert B.check_project_backlinks() == [], B.check_project_backlinks()


def test_source_line_in_first_paragraph_satisfies():
    """没写 related、但首段开头写显式「来源:本项目」→ 合格(约定留的人话出口)。

    两种形态都要认:带前导装饰 + 括号补充的 `> **来源:本项目(真库)**`,和裸行声明。
    """
    for body in ("> **来源:本项目(真库)**\n\n正文。", "来源:本项目\n\n正文。"):
        with tempfile.TemporaryDirectory() as d:
            L.VAULT_ROOT = Path(d)
            _project(L.VAULT_ROOT, body=body)
            assert B.check_project_backlinks() == [], (body, B.check_project_backlinks())


def test_source_fragment_inside_sentence_rejected():
    """声明只在首段行首算数:叙述句里夹带「来源:本项目」→ 仍报 A13。

    变异证据:把 `_says_source` 退回旧版(RE 去掉 `^` 与冒号、并改回 `SOURCE_RE.search`)
    → 叙述句被误认成声明 → 本用例变红。
    """
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT, body="正文取自 来源:本项目 之外的工具。")
        got = B.check_project_backlinks()
        assert [f.path for f in got] == ["10-项目/甲/20-知识/x.md"], got


def test_h2_first_note_has_no_first_paragraph():
    """无 H1、第一个结构就是 `## 背景` 的笔记:标题下的正文不算首段 → 报 A13。

    变异证据:把 `_first_paragraph` 退回宽松版(无 H1 时把首个 `## ` 当标题跳过、其正文当首段)
    → 本用例变红。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root)
        _mk(root, "10-项目/甲/20-知识/x.md",
            "---\ntype: note\nstatus: learning\n---\n\n## 背景\n\n来源:本项目\n")
        got = B.check_project_backlinks()
        assert [f.path for f in got] == ["10-项目/甲/20-知识/x.md"], got


def test_source_line_out_of_first_paragraph_rejected():
    """「来源:本项目」写在 `## 背景` 小节里不算首段 —— 首段 = 标题之后的第一段正文。"""
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT, body="## 背景\n\n来源:本项目\n")
        got = B.check_project_backlinks()
        assert len(got) == 1 and got[0].stage == "A13", got


def test_each_note_judged_separately():
    """同一项目两篇笔记只缺一篇 → 只报缺的那篇(逐篇判,合格篇不掩护漏篇)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, fm=RELATED)
        _mk(root, "10-项目/甲/20-知识/y.md", NOTE % ("", "正文,不提来源。"))
        got = B.check_project_backlinks()
        assert [f.path for f in got] == ["10-项目/甲/20-知识/y.md"], got


def test_missing_index_attributed_to_a4():
    """有笔记但项目 `00-索引.md` 未建 → A13 不报(同因单报),由 A4 报「项目索引缺失」。"""
    with tempfile.TemporaryDirectory() as d:
        L.VAULT_ROOT = Path(d)
        _project(L.VAULT_ROOT, fm=RELATED, index=False)
        assert B.check_project_backlinks() == [], B.check_project_backlinks()
        a4 = C.check_moc_coverage()
        assert [(f.stage, f.path, f.detail) for f in a4] == \
            [("A4", "10-项目/甲/00-索引.md", "项目索引缺失")], a4


def test_empty_knowledge_dir_is_silent():
    """`20-知识/` 只有 .gitkeep(无笔记)→ A13 不报(反向边不存在,索引缺失同上归 A4)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, index=False, note=False)
        _mk(root, "10-项目/甲/20-知识/.gitkeep", "")
        assert B.check_project_backlinks() == [], B.check_project_backlinks()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
