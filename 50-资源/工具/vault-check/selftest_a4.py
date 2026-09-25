#!/usr/bin/env python3
"""A4(项目索引覆盖)自检:临时假库里验 `20-知识/` 必须被项目 `00-索引.md` 收录。

旧口径(20-领域 / 50-资源 是否出现在 `00-索引/*.md`)随旧 MOC 删除退役(2026-09-25 Task 8)。
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


def test_a4_no_longer_covers_30_resources():
    """旧口径退役:`50-资源` 笔记未出现在任何 MOC 也不再报 A4(改由项目/容器索引「原料」块与 A3 守)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/系统.md", "---\ntype: note\nstatus: done\n---\n[x](<../50-资源/其他.md>)\n")
        _mk(root, "50-资源/记录/r.md", "---\ntype: log\nstatus: done\n---\nx\n")
        assert not C.check_moc_coverage(), C.check_moc_coverage()


def test_a4_project_index_coverage():
    """项目 20-知识/ 里的笔记未在项目 00-索引.md 登记 → 报 A4;缺索引也报一条。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/git/00-索引.md", "# 索引\n")
        _mk(root, "10-项目/git/20-知识/Git.md", "---\ntype: system\nstatus: learning\n---\n# Git\n")
        _mk(root, "10-项目/noidx/20-知识/x.md", "---\ntype: note\nstatus: done\n---\nx\n")
        got = [f.path for f in C.check_moc_coverage()]
        assert got == ["10-项目/git/20-知识/Git.md", "10-项目/noidx/00-索引.md"], got


def test_a4_project_index_ok_when_listed():
    """项目索引里按主干登记过 → 不报(标题可与文件名不同)。

    索引里刻意只写主干 `[[Git]]`(Obsidian 双链省略 .md),并用断言钉死索引文本
    不含 "Git.md":若实现退回整名匹配(`p.name not in idx`),本用例必红。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        idx = "# 索引\n\n- [[Git]] — Git 基础 | learning\n"
        _mk(root, "10-项目/git/00-索引.md", idx)
        _mk(root, "10-项目/git/20-知识/Git.md", "---\ntype: system\nstatus: learning\n---\n# Git\n")
        assert "Git.md" not in idx, "索引里不得出现整名,否则锁不住主干匹配"
        assert L.project_knowledge_dirs(root) == [("git", root / "10-项目/git/20-知识")], "应识别出项目知识目录"
        assert not C.check_moc_coverage(), C.check_moc_coverage()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
