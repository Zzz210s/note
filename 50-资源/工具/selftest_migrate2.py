#!/usr/bin/env python3
"""迁移工具自检(第二批):计划表完整性 / 同名消歧 / A13 来源声明 / 相对链接重锚 / 空根删除。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note && python -B 50-资源/工具/selftest_migrate2.py

这些都对应 Task 6/7 实测踩到的坑:两个西语 `不规则动词.md` 撞名、搬完 `20-领域` 空壳还在、
搬家笔记里指向**没被搬走**的目标(模板 / 每日笔记 / 50-资源 素材)的相对路径层级数对不上
(Task 7 第一遍漏了 7 条 A1)。第一批(`selftest_migrate.py`)测 `<...>` 包裹与源缺失退出码。
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent          # 50-资源/工具
sys.path.insert(0, str(TOOLS))
import migrate_engine as E                                            # noqa: E402
from migrate_plan import GROUPED_CONTAINERS, GROUPED_PROJECTS, OLD_TO_NEW, RENAMES  # noqa: E402
from migrate_rewrite import rewrite_file                              # noqa: E402

_SPEC = importlib.util.spec_from_file_location("migrate_notes", TOOLS / "migrate-notes.py")
assert _SPEC and _SPEC.loader                    # 文件名带连字符,只能按路径加载
M = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(M)


def _sandbox(root: Path) -> None:
    """把两个模块的 VAULT 一起指到临时库:engine 的 rel() 也按 VAULT 算。"""
    E.VAULT = M.VAULT = root


def test_plan_table_covers_55_rows():
    """计划表要齐:容器 22 + 项目 33,且目标路径两两不同(同名撞车会当场覆盖)。"""
    assert sum(len(v) for v in GROUPED_CONTAINERS.values()) == 22
    assert sum(len(v) for v in GROUPED_PROJECTS.values()) == 33
    tgts = list(OLD_TO_NEW.values())
    assert len(tgts) == len(set(tgts)) == 55, [t for t in tgts if tgts.count(t) > 1]


def test_rename_disambiguates_same_filename():
    """西语通用版与 A1 教材版同名 `不规则动词.md` → 教材版加 `(A1)` 后缀(库规先例)。"""
    a1 = "20-领域/08-外语/西班牙语/4-教材笔记/水木外语-西班牙语/A1/语法/不规则动词.md"
    old = "20-领域/08-外语/西班牙语/2-词汇/不规则动词.md"
    assert RENAMES == {a1: "不规则动词(A1).md"}
    assert OLD_TO_NEW[a1].endswith("/不规则动词(A1).md"), OLD_TO_NEW[a1]
    assert OLD_TO_NEW[old].endswith("/不规则动词.md"), OLD_TO_NEW[old]


def test_declare_line_then_array_then_idempotent():
    """A13 来源声明:无 `related` 新增一行;已有则转数组保留原值;重复跑不再改;dry-run 不写盘。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        old_vault = E.VAULT
        _sandbox(root)
        try:
            p = root / "x.md"
            p.write_bytes(b"---\ntype: language\nstatus: done\n---\n\n# x\n")
            assert E._declare_file(p, "甲", True) == 1
            assert 'related: "[[甲/!项目说明|项目]]"' in p.read_text(encoding="utf-8")
            assert E._declare_file(p, "甲", True) == 0            # 幂等
            before = p.read_bytes()
            assert E._declare_file(p, "甲", False) == 0 and p.read_bytes() == before
            q = root / "y.md"
            q.write_bytes(b"---\ntype: language\nrelated: \"[[x]]\"\n---\n\n# y\n")
            assert E._declare_file(q, "甲", True) == 1
            assert 'related: ["[[x]]", "[[甲/!项目说明|项目]]"]' in q.read_text(encoding="utf-8")
        finally:
            E.VAULT = old_vault


def test_declare_keeps_crlf_frontmatter():
    """CRLF 文件:声明行按 `\\r\\n` 拼,整个文件不出现孤立 `\\n`(库里有 8 篇 CRLF)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        old_vault = E.VAULT
        _sandbox(root)
        try:
            p = root / "y.md"
            p.write_bytes("---\r\ntype: tutorial\r\nstatus: done\r\n---\r\n\r\n# y\r\n".encode("utf-8"))
            assert E._declare_file(p, "甲", True) == 1
            text = p.read_bytes().decode("utf-8")     # read_text 会做通用换行转换,看不出 CRLF
            assert 'related: "[[甲/!项目说明|项目]]"\r\n' in text, repr(text)
            assert "\n" not in text.replace("\r\n", ""), repr(text)
        finally:
            E.VAULT = old_vault


def test_rebase_reanchors_unmoved_target():
    """搬家笔记指向未搬家目标的相对链接按新家重算(旧深度 → 新深度)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        old_dir = root / "old/x/y"
        new_dir = root / "newdir/z"
        (root / "tpl").mkdir()
        (root / "tpl/t.md").write_bytes(b"x\n")
        old_dir.mkdir(parents=True)
        (old_dir / "n.md").write_text("[模版](../../../tpl/t.md)\n", encoding="utf-8")
        new_dir.mkdir(parents=True)
        dst = new_dir / "n.md"
        dst.write_bytes((old_dir / "n.md").read_bytes())          # 已搬到新家
        hits = rewrite_file(dst, {}, {}, {}, {dst.resolve(): old_dir}, True)
        assert hits == 1, hits
        assert dst.read_text(encoding="utf-8") == "[模版](../../tpl/t.md)\n", dst.read_text(encoding="utf-8")


def test_prune_empty_removes_domain_root():
    """搬空的 `20-领域` 本身也要删(rglob 不含自己,故显式补在队列末尾)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        old_vault = E.VAULT
        _sandbox(root)
        try:
            f = root / "20-领域/甲/x.md"
            f.parent.mkdir(parents=True)
            f.write_bytes(b"x\n")
            moves = {"20-领域/甲/x.md": "10-项目/p/20-知识/x.md"}
            assert M.prune_empty(moves, False) == ["20-领域/甲", "20-领域"]   # 预演:按 moves 预判
            f.unlink()                                              # 真实链路里已先 git mv 走
            assert M.prune_empty(moves, True) == ["20-领域/甲", "20-领域"]
            assert not (root / "20-领域").exists()
        finally:
            E.VAULT = old_vault


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
