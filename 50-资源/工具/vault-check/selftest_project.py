#!/usr/bin/env python3
"""A7/A9 项目引导口径自检:路线取数含项目索引、统计行对齐项目索引页。"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_project as P


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _project(root: Path, name: str, status: str = "learning") -> None:
    """一个内部有产出的项目:!项目说明.md + 20-知识/<name>.md(status 与实物一致)。"""
    _mk(root, "10-项目/%s/!项目说明.md" % name,
        "---\ntype: project\nstatus: %s\n---\n# %s\n" % (status, name))
    _mk(root, "10-项目/%s/20-知识/%s.md" % (name, name),
        "---\ntype: system\nstatus: %s\n---\n# %s\n" % (status, name))


def test_a7_project_index_is_route_source():
    """项目索引的路线小节里链接到的项目算「已进路线」,即便旧 MOC 没列它。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "00-索引/系统.md", "---\ntype: note\nstatus: done\n---\n## 学习路线\n\n(空)\n")
        _project(root, "docker")
        _project(root, "k8s")
        _mk(root, "10-项目/k8s/00-索引.md",
            "# k8s 索引\n\n## 计划与进度\n\n- [ ] 前置:[Docker](<../docker/!项目说明.md>)\n")
        got = P.check_roadmap()
        assert not [f for f in got if "docker" in f.detail], got
        assert any("k8s" in f.detail and "未进路线" in f.detail for f in got), got


def test_a7_root_index_lists_projects():
    """新结构:根 00-索引.md 的 `## 计划与进度` 列出全部项目 → A7 干净。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "docker")
        _project(root, "k8s")
        _mk(root, "00-索引.md",
            "# 索引\n\n## 计划与进度\n\n- [Docker](<10-项目/docker/!项目说明.md>)\n"
            "- [K8s](<10-项目/k8s/!项目说明.md>)\n")
        assert not P.check_roadmap(), P.check_roadmap()


def test_a7_legacy_moc_still_checked():
    """旧口径不得回归:系统.md 路线里指向不存在项目的链接仍要报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "docker")
        _mk(root, "00-索引/系统.md", "---\ntype: note\nstatus: done\n---\n## 学习路线\n\n"
            "- [ ] [Docker](<../10-项目/docker/!项目说明.md>)\n"
            "- [ ] [幽灵](<../10-项目/幽灵/!项目说明.md>)\n")
        got = P.check_roadmap()
        assert any("../10-项目/幽灵/!项目说明.md" == f.detail for f in got), got
        assert not [f for f in got if "未进路线" in f.detail], got


def test_a9_project_index_stats_mismatch():
    """项目索引统计行的篇数与实物不符 → 报 A9。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "git")
        _mk(root, "10-项目/git/00-索引.md",
            "# git 索引\n\n> 本项目知识 5 篇 · 状态 learning · 覆盖 1/1(100%)\n\n- [[Git]]\n")
        got = P.check_index_stats()
        assert any("知识 5 篇" in f.detail for f in got), got


def test_a9_project_index_stats_ok():
    """统计行篇数/状态/覆盖都与实物一致 → 不报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "git")
        _mk(root, "10-项目/git/00-索引.md",
            "# git 索引\n\n> 本项目知识 1 篇 · 状态 learning · 覆盖 1/1(100%)\n\n- [[Git]]\n")
        assert not P.check_index_stats(), P.check_index_stats()


def test_a9_root_summary_equals_project_sum():
    """根索引汇总行的知识数与各项目之和不符 → 报 A9。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "git")
        _mk(root, "00-索引.md", "# 索引\n\n> 全库知识 7 篇 · 项目 1 个\n")
        got = P.check_index_stats()
        assert any("各项目之和 1" in f.detail for f in got), got


def test_a9_root_summary_ok():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "git")
        _mk(root, "00-索引.md", "# 索引\n\n> 全库知识 1 篇 · 项目 1 个\n")
        assert not P.check_index_stats(), P.check_index_stats()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))