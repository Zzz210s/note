#!/usr/bin/env python3
"""check_vault 自检:在临时目录里造假库,验证各检查项能抓到问题。"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import check_vault as C
import checks_extra as X

def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p

def test_detects_broken_link_and_orphan_and_meta():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/x.md", "---\ntype: note\nstatus: done\n---\n- [A](<../20-领域/a.md>)\n")
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
        _mk(root, "00-索引/x.md", "---\ntype: note\nstatus: done\n---\n[[!项目说明]] [[冒泡算法]]\n")
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/乙/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "20-领域/冒泡算法.md", "---\ntype: algorithm\nstatus: done\n---\nx\n")
        got = {f.path for f in C.check_orphans()}
        assert "10-项目/甲/!项目说明.md" in got and "10-项目/乙/!项目说明.md" in got, got
        assert "20-领域/冒泡算法.md" not in got, got

def test_a4_also_covers_30_resources():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/x.md", "---\ntype: note\nstatus: done\n---\n[a](<../20-领域/a.md>)\n")
        _mk(root, "20-领域/a.md", "---\ntype: note\nstatus: done\n---\nx\n")
        _mk(root, "50-资源/r.md", "---\ntype: log\nstatus: done\n---\nx\n")
        got = C.check_moc_coverage()
        assert {f.path for f in got} == {"50-资源/r.md"}, got

def test_a7_flags_missing_link_and_status_mismatch():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/系统.md", "---\ntype: note\nstatus: done\n---\n## 学习路线\n\n"
            "[有内容](<../10-项目/有内容/!项目说明.md>)\n"
            "[不存在](<../10-项目/不存在/!项目说明.md>)\n")
        _mk(root, "10-项目/有内容/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/有内容/n.md", "---\ntype: note\nstatus: done\n---\nx\n")
        _mk(root, "10-项目/空项目/!项目说明.md", "---\ntype: project\nstatus: learning\n---\nx\n")
        got = L.check_roadmap()
        assert any(f.detail == "../10-项目/不存在/!项目说明.md" for f in got), got
        assert any("有内容" in f.path and "应为 learning" in f.detail for f in got), got
        assert any("空项目" in f.path and "应为 todo" in f.detail for f in got), got
        assert any("未进学习路线" in f.detail and "空项目" in f.detail for f in got), got


def test_a7_counts_impl_plan_as_project_content():
    """!实施计划.md 算「项目内已有产出」,使 status=learning 成立(设计文档决策 3(c))。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/系统.md", "---\ntype: note\nstatus: done\n---\n## 学习路线\n\n"
            "- [ ] [甲](<../10-项目/甲/!项目说明.md>)\n"
            "- [ ] [乙](<../10-项目/乙/!项目说明.md>)\n")
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: learning\n---\nx\n")
        _mk(root, "10-项目/甲/!实施计划.md", "---\ntype: note\nstatus: learning\n---\nx\n")
        _mk(root, "10-项目/乙/!项目说明.md", "---\ntype: project\nstatus: learning\n---\nx\n")
        got = L.check_roadmap()
        assert not [f for f in got if f.path.startswith("10-项目/甲/")], got
        assert any(f.path.startswith("10-项目/乙/") and "应为 todo" in f.detail for f in got), got


def test_a7_skips_project_without_frontmatter():
    """缺 frontmatter 的项目由 A6 报,A7 不得再报一条空 status 的重复项。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/系统.md", "---\ntype: note\nstatus: done\n---\n## 学习路线\n\n"
            "- [ ] [丙](<../10-项目/丙/!项目说明.md>)\n")
        _mk(root, "10-项目/丙/!项目说明.md", "# 丙\n无 frontmatter\n")
        assert not L.check_roadmap(), L.check_roadmap()


def test_a7_ignores_skipped_dirs():
    """项目内 .superpowers/ docs/ .trash/ 里的 md 不算产出(todo 不该被误报成 learning)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/系统.md", "---\ntype: note\nstatus: done\n---\n## 学习路线\n\n"
            "- [ ] [丁](<../10-项目/丁/!项目说明.md>)\n")
        _mk(root, "10-项目/丁/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/丁/docs/spec.md", "---\ntype: note\nstatus: done\n---\nx\n")
        _mk(root, "10-项目/丁/.superpowers/plan.md", "---\ntype: note\nstatus: done\n---\nx\n")
        assert not L.check_roadmap(), L.check_roadmap()

def test_a8_flags_case_variant_tag():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "20-领域/a.md", "---\ntype: note\nstatus: done\ntags: [windows, 终端]\n---\nx\n")
        _mk(root, "20-领域/b.md", "---\ntype: note\nstatus: done\ntags: [Windows]\n---\nx\n")
        got = X.check_tags()
        assert len(got) == 1 and "Windows" in got[0].detail, got

def test_a8_ignores_unique_case():
    """专名(只有大写一种写法,例如 LInux/ABCD 式)不应被报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "20-领域/a.md", "---\ntype: note\nstatus: done\ntags: [RFID, 硬件]\n---\nx\n")
        assert not X.check_tags(), X.check_tags()

def test_a9_flags_entry_count_mismatch():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/算法.md", "# 算法 MOC\n\n> 条目 5 · 覆盖 20-领域/01-算法 1/1(100%)· 最后校验 2026-09-23\n\n"
            "- [冒泡](<../20-领域/01-算法与数据结构/冒泡.md>) — x | done\n")
        _mk(root, "20-领域/01-算法与数据结构/冒泡.md", "---\ntype: algorithm\nstatus: done\n---\nx\n")
        got = X.check_moc_stats()
        assert any("条目 5" in f.detail for f in got), got

def test_a9_passes_when_consistent():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/算法.md", "# 算法 MOC\n\n> 条目 1 · 覆盖 20-领域/01-算法 1/1(100%)· 最后校验 2026-09-23\n\n"
            "- [冒泡](<../20-领域/01-算法与数据结构/冒泡.md>) — x | done\n")
        _mk(root, "20-领域/01-算法与数据结构/冒泡.md", "---\ntype: algorithm\nstatus: done\n---\nx\n")
        assert not X.check_moc_stats(), X.check_moc_stats()

def test_a10_flags_knowledge_type_in_project_layer():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/甲/2026-01-01-题解.md", "---\ntype: algorithm\nstatus: done\n---\nx\n")
        got = X.check_project_layer_types()
        assert len(got) == 1 and "algorithm" in got[0].detail, got

def test_a10_allows_project_note_and_log():
    """项目层的脚手架/每日笔记/记录是合规的(README 已如此定义),不得误报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/甲/08-每日笔记/2026-09-01.md", "---\ntype: note\nstatus: done\n---\nx\n")
        _mk(root, "10-项目/甲/岗位池.md", "---\ntype: log\nstatus: learning\n---\nx\n")
        _mk(root, "10-项目/!问题追踪/a.md", "# 无 frontmatter\n")
        assert not X.check_project_layer_types(), X.check_project_layer_types()

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
