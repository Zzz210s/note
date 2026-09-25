#!/usr/bin/env python3
"""extras 类自检:A8 标签规范 / A10 知识归属(项目与容器)。

A1~A6 在 `selftest_check.py`,A4 在 `selftest_a4.py`,A7 与项目口径 A9(统计行)在
`selftest_project*.py`。按主题拆文件只为一件事:每个自研文件守住 ≤200 行。
旧 MOC 统计块(A9 的 MOC 口径)在 2026-09-25 收尾轮随 `00-索引/` 一并删除,
那两个用例也随之删去。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_extra as X

def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p

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

def test_a10_project_root_knowledge_must_move_into_knowledge_dir():
    """(反转)项目根下散放知识类正文 → 报『应放 20-知识/』。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/甲/Git原理.md", "---\ntype: system\nstatus: learning\n---\nx\n")
        got = X.check_project_layer_types()
        assert len(got) == 1 and "20-知识/" in got[0].detail, got

def test_a10_knowledge_dir_is_compliant():
    """(反转)知识类正文放在 20-知识/ 里 → 合规(旧判据会把每篇都误报)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: todo\n---\nx\n")
        _mk(root, "10-项目/甲/20-知识/Git原理.md", "---\ntype: system\nstatus: learning\n---\nx\n")
        _mk(root, "10-项目/甲/20-知识/深挖/索引实现.md", "---\ntype: concept\nstatus: done\n---\nx\n")
        assert not X.check_project_layer_types(), X.check_project_layer_types()

def test_a10_container_knowledge_dir_is_compliant():
    """容器的 20-知识/ 同样合规;容器根下散放知识类正文照样报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!名词解释/20-知识/并发.md", "---\ntype: concept\nstatus: done\n---\nx\n")
        assert not X.check_project_layer_types(), X.check_project_layer_types()
        _mk(root, "10-项目/!名词解释/幂等.md", "---\ntype: concept\nstatus: done\n---\nx\n")
        got = X.check_project_layer_types()
        assert len(got) == 1 and got[0].path == "10-项目/!名词解释/幂等.md", got

def test_a10_knowledge_dir_needs_project_owner():
    """`10-项目/20-知识/` 直接挂在项目层下(不属于任何项目/容器)→ 仍须报。

    设计口径是「知识必须住某个项目或容器的 `20-知识/`」,路径形如
    `10-项目/<某个目录>/20-知识/…`;只看「路径里有没有 `/20-知识/`」会把它放行。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/20-知识/校验.md", "---\ntype: concept\nstatus: done\n---\nx\n")
        got = X.check_project_layer_types()
        assert len(got) == 1 and "20-知识/" in got[0].detail, got

def test_a10_other_project_subdir_still_reported():
    """项目里的其它子目录(如 08-每日笔记/)不是知识归属地 → 知识类正文照样报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/08-每日笔记/Git.md", "---\ntype: system\nstatus: learning\n---\nx\n")
        got = X.check_project_layer_types()
        assert len(got) == 1 and got[0].path == "10-项目/甲/08-每日笔记/Git.md", got
        assert "20-知识/" in got[0].detail, got

def test_a10_note_and_log_allowed_outside_knowledge_dir():
    """note/log/project 不在检查范围,放项目根或子目录都合规。"""
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
