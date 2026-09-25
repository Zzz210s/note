#!/usr/bin/env python3
"""迁移工具自检:①引用改写的 `<...>` 包裹规则(F1)②源缺失必须非零退出(F2)。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note && python -B 50-资源/工具/selftest_migrate.py

这两条都是 Task 7 会真实踩到的分支:西语目录名带空格(裸 `](a b.md)` 会断链)、
迁移表里路径写错(旧版只打印一句就返回 0,看着像成功)。
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

TOOLS = Path(__file__).resolve().parent          # 50-资源/工具
sys.path.insert(0, str(TOOLS))
from migrate_rewrite import md_link, rewrite_file                      # noqa: E402

_SPEC = importlib.util.spec_from_file_location("migrate_notes", TOOLS / "migrate-notes.py")
assert _SPEC and _SPEC.loader                    # 文件名带连字符,只能按路径加载
M = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(M)


def _rewrite(reader: Path, body: str, old: Path, new: Path) -> tuple[int, str]:
    """让 `reader` 里指向 `old` 的引用改写为指向新家 `new`(搬家文件不必真存在)。"""
    reader.parent.mkdir(parents=True, exist_ok=True)
    reader.write_bytes(body.encode("utf-8"))
    n = rewrite_file(reader, {old.resolve(): new.resolve()}, {}, {old.name: "x"}, {}, True)
    return n, reader.read_text(encoding="utf-8")


def test_md_link_forces_brackets_on_space_or_non_ascii():
    """规则表:含空格/非 ASCII 强制包裹,原本带 `<>` 的保持,纯 ASCII 保持裸写。"""
    assert md_link("../2026-掌握西班牙语 B2/词.md", False) == "](<../2026-掌握西班牙语 B2/词.md>)"
    assert md_link("../20-知识/概念.md", False) == "](<../20-知识/概念.md>)"      # 中文路径也要包
    assert md_link("../new/a.md", False) == "](../new/a.md)"
    assert md_link("../new/a.md", True) == "](<../new/a.md>)"                     # 原样保持
    assert md_link("../new/a b.md#锚", True) == "](<../new/a b.md#锚>)"           # 锚点一起包


def test_bare_link_to_spaced_target_gets_brackets():
    """F1①:裸 `](../20-领域/x.md)` 改写到带空格的新家 → 必须 `](<… 西班牙语 B2/x.md>)`。

    西语项目目录名带空格,而待改写的**旧**链接里没有空格(所以 LINK_RE 能匹配) ——
    不强制包裹就会产出 `](../2026-掌握西班牙语 B2/x.md)`,Markdown 从这里断掉。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        n, text = _rewrite(root / "00-索引/索引.md", "[教材](../20-领域/语法.md) 与 [外部](https://example.com/a)\n",
                           root / "20-领域/语法.md",
                           root / "10-项目/2026-掌握西班牙语 B2/20-知识/语法.md")
        assert n == 1, n
        assert "](<../10-项目/2026-掌握西班牙语 B2/20-知识/语法.md>)" in text, text
        assert "](https://example.com/a)" in text, text                   # 外链不动


def test_bare_link_to_non_ascii_target_gets_brackets():
    """F1①(非 ASCII 半边):目标路径不含空格、但含中文 → 同样强制包裹。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        n, text = _rewrite(root / "00-索引/索引.md", "[同目录](../20-领域/note.md)\n",
                           root / "20-领域/note.md", root / "10-项目/proj/note.md")
        assert n == 1 and "](<../10-项目/proj/note.md>)" in text, (n, text)


def test_bracketed_link_stays_bracketed():
    """F1②:原本 `](<path>)` 的写法保持包裹(新路径不需要包裹时也不退化)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        n, text = _rewrite(root / "00-索引/索引.md", "[同目录](<../20-领域/note.md>)\n",
                           root / "20-领域/note.md", root / "new/note.md")
        assert n == 1 and "](<../new/note.md>)" in text, (n, text)


def test_pure_ascii_target_stays_bare():
    """F1③:纯 ASCII 且无空格 → 保持裸写(不强加 `<>`)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        n, text = _rewrite(root / "00-索引/索引.md", "[同目录](../20-领域/note.md)\n",
                           root / "20-领域/note.md", root / "new/note.md")
        assert n == 1 and "](../new/note.md)" in text and "<" not in text, (n, text)


def test_find_missing_flags_wrong_path():
    """F2 单元:旧、新位置都不存在 → 判为缺失。"""
    with tempfile.TemporaryDirectory() as d:
        old_vault, M.VAULT = M.VAULT, Path(d)
        try:
            moves = {"20-领域/没写对路径.md": "10-项目/!名词解释/20-知识/没写对路径.md"}
            assert M.find_missing(moves) == ["20-领域/没写对路径.md"], M.find_missing(moves)
        finally:
            M.VAULT = old_vault


def test_find_missing_accepts_already_migrated():
    """F2 单元:「旧没了但新在」是 apply 后复跑的合法状态,不算缺失(幂等的前提)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        old_vault, M.VAULT = M.VAULT, root
        try:
            dst = root / "10-项目/!名词解释/20-知识/已搬.md"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(b"x\n")
            assert M.find_missing({"20-领域/已搬.md": "10-项目/!名词解释/20-知识/已搬.md"}) == []
        finally:
            M.VAULT = old_vault


def test_missing_source_exits_nonzero_in_dry_run():
    """F2 端到端:dry-run 遇源缺失 → 非零退出 + 明确错误(旧版打印一句就 return 0)。"""
    with tempfile.TemporaryDirectory() as d:
        old_vault, old_table = M.VAULT, M.OLD_TO_NEW
        M.VAULT = Path(d)
        M.OLD_TO_NEW = {"20-领域/没写对路径.md": "10-项目/!名词解释/20-知识/没写对路径.md"}
        err = io.StringIO()
        try:
            with redirect_stderr(err):
                rc = M.main(["--dry-run", "--filter", "!名词解释"])
        finally:
            M.VAULT, M.OLD_TO_NEW = old_vault, old_table
        assert rc != 0, "源缺失仍返回 0(静默成功)"
        assert "没写对路径.md" in err.getvalue(), err.getvalue()
        assert "已中止" in err.getvalue(), err.getvalue()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
