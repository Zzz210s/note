#!/usr/bin/env python3
"""A14(索引页一致性)自检之二:项目索引的知识链接数(判据②),以及它与 A4/A9 的分工
(同因单报),外加新结构端到端。

拆出本文件是因为 `selftest_index.py` 已装下判据①与提示通道,两者合起来会越过 200 行上限。
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


def _project(root: Path, name: str, notes: int = 1) -> None:
    """一个带 `20-知识/` 的项目(说明 + notes 篇知识笔记);项目索引页由用例自己写。"""
    _mk(root, "10-项目/%s/!项目说明.md" % name,
        "---\ntype: project\nstatus: learning\n---\n\n# %s\n" % name)
    for i in range(1, notes + 1):
        _mk(root, "10-项目/%s/20-知识/知识%d.md" % (name, i),
            "---\ntype: note\nstatus: learning\nrelated: \"[[%s/!项目说明|项目]]\"\n---\n\n# 知识%d\n"
            % (name, i))


def test_link_count_mismatch_reported():
    """索引把两篇知识都写了名字(A4 过),但只给了一篇文件链接 → A14 报计数不符(1 vs 2)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", notes=2)
        _mk(root, "10-项目/甲/00-索引.md", "---\ntype: note\nstatus: learning\n---\n\n# 甲\n\n"
            "- [知识1](<20-知识/知识1.md>)\n- 知识2(待补链接)\n")
        assert C.check_moc_coverage() == [], C.check_moc_coverage()      # A4 已通过
        assert [f.detail for f in I.check_project_index_links()] == [
            "项目索引的知识文件链接 1 个与 20-知识 实物 2 篇不符"], I.check_project_index_links()


def test_duplicate_link_mismatch_reported():
    """都登记了、但同一篇链了两次 → 3 个链接 vs 2 篇实物,A14 报计数不符。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", notes=2)
        _mk(root, "10-项目/甲/00-索引.md", "---\ntype: note\nstatus: learning\n---\n\n# 甲\n\n"
            "- [[知识1]]\n- [[知识1]]\n- [[知识2]]\n")
        assert [f.detail for f in I.check_project_index_links()] == [
            "项目索引的知识文件链接 3 个与 20-知识 实物 2 篇不符"], I.check_project_index_links()


def test_link_count_ok_for_markdown_and_wikilink():
    """两种链接写法都算数:markdown 相对路径 + 裸双链;数目对上 → 0 处。

    指向别处的链接(说明 / 别的项目)不参与计数,所以它们不该把数字顶上去。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", notes=2)
        _project(root, "乙")
        index = _mk(root, "10-项目/甲/00-索引.md",
            "---\ntype: note\nstatus: learning\n---\n\n# 甲\n\n"
            "- [知识1](<20-知识/知识1.md>)\n- [[知识2]]\n"
            "- 说明见 [!项目说明](<!项目说明.md>)\n- 参考 [乙的知识](../乙/20-知识/知识1.md)\n")
        kd = root / "10-项目/甲/20-知识"
        assert I.knowledge_link_count(index, kd) == 2, I.knowledge_link_count(index, kd)
        assert I.check_project_index_links() == [], I.check_project_index_links()


def test_missing_entry_is_a4_only():
    """有笔记只被写进正文、连名字都没进索引 → 该 A4 报「未登记」,A14 一条都不出。

    同时把 A4 的口径(主干是否出现在索引全文)与本文件 `unlisted_notes()` 锁在一起:
    两边一旦口径漂移,这里就红。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", notes=2)
        text = "---\ntype: note\nstatus: learning\n---\n\n# 甲\n\n- [知识1](<20-知识/知识1.md>)\n"
        _mk(root, "10-项目/甲/00-索引.md", text)
        a4 = [f for f in C.check_moc_coverage() if f.path.startswith("10-项目/甲")]
        assert [f.path for f in a4] == ["10-项目/甲/20-知识/知识2.md"], a4
        assert [L.rel_path(p) for p in I.unlisted_notes(root / "10-项目/甲/20-知识", text)] \
            == [f.path for f in a4]
        assert I.check_index_consistency() == [], I.check_index_consistency()


def test_missing_project_index_is_a4_only():
    """项目缺 `00-索引.md` → A4 报「项目索引缺失」,A14 不重复。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        assert [f.detail for f in C.check_moc_coverage()] == ["项目索引缺失"], C.check_moc_coverage()
        assert I.check_project_index_links() == [], I.check_project_index_links()


def test_stat_line_mismatch_is_a9_only():
    """统计行篇数不对(链接数是对的)→ A9 报,A14 不掺和(计划原文的 ③ 整体归 A9)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        _mk(root, "10-项目/甲/00-索引.md", "---\ntype: note\nstatus: learning\n---\n\n# 甲\n\n"
            "> 本项目知识 5 篇 · 状态 learning · 覆盖 5/5(100%)\n\n"
            "- [知识1](<20-知识/知识1.md>)\n")
        assert any("统计行知识 5 篇与实物 1 不符" in f.detail for f in P.check_index_stats()), \
            P.check_index_stats()
        assert I.check_index_consistency() == [], I.check_index_consistency()


# ---------- 新结构端到端 ----------

MISSION = "## Why\n\nx\n\n## Success looks like\n\nx\n\n## Constraints\n\nx\n\n## Out of scope\n\nx\n"
RESOURCES = "## Knowledge\n\nx\n\n## Gaps\n\nx\n"


def test_new_structure_end_to_end_passes():
    """新结构全绿一套(根索引 + 项目索引 + 20-知识 + 容器)→ rc=0,A14 为 0 处。

    知识笔记刻意用 `type: note`:A10 的「反转」(知识必须住 20-知识)还没落地,现在写
    `type: system` 会被 A10 拦下,那是后续任务的事,不该污染本用例的 A14 结论。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: learning\n---\n\n# 甲\n")
        _mk(root, "10-项目/甲/MISSION.md", MISSION)
        _mk(root, "10-项目/甲/RESOURCES.md", RESOURCES)
        _mk(root, "10-项目/甲/20-知识/知识1.md",
            "---\ntype: note\nstatus: learning\nrelated: \"[[甲/!项目说明|项目]]\"\n---\n\n# 知识1\n")
        _mk(root, "10-项目/甲/00-索引.md", "---\ntype: note\nstatus: learning\n---\n\n# 甲\n\n"
            "> 本项目知识 1 篇 · 状态 learning · 覆盖 1/1(100%)\n\n- 全局入口:[索引](<../../00-索引.md>)\n\n"
            "## 知识产出\n\n- [知识1](<20-知识/知识1.md>)\n")
        _mk(root, "10-项目/!名词解释/00-索引.md", "---\ntype: note\nstatus: done\n---\n\n# 名词解释\n")
        _mk(root, "00-索引.md", "---\ntype: note\nstatus: done\n---\n\n# 索引\n\n"
            "> 全库知识 1 篇 · 项目 1 个\n\n## 计划与进度\n\n- [[10-项目/甲/!项目说明|甲]]\n\n"
            "## 项目清单\n\n- [甲](<10-项目/甲/00-索引.md>) · learning · 1 篇\n"
            "- [名词解释](<10-项目/!名词解释/00-索引.md>)\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = C.main(["--quiet"])
        text = buf.getvalue()
        assert "[A14 索引页一致性] 0 处" in text, text
        assert "结论:PASS" in text and rc == 0, (rc, text)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
