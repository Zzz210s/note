#!/usr/bin/env python3
"""A7/A9 项目引导口径自检:路线取数含项目索引、项目清单认双链、统计行对齐项目索引页。"""
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
    """项目索引的路线小节里链接到的项目算「已进路线」,即便根索引没列它。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
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


def test_a7_forward_check_reports_broken_project_link():
    """正向检查不得回归:来源页(根 `00-索引.md`)里指向不存在项目的链接必须报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "docker")
        _mk(root, "00-索引.md", "# 索引\n\n## 计划与进度\n\n"
            "- [Docker](<10-项目/docker/!项目说明.md>)\n"
            "- [幽灵](<10-项目/幽灵/!项目说明.md>)\n")
        got = P.check_roadmap()
        assert any("10-项目/幽灵/!项目说明.md" == f.detail for f in got), got
        assert not [f for f in got if "未进路线" in f.detail], got


def test_a7_wikilink_project_entry():
    """M3:根索引用 wikilink 列项目也算已进路线(旧实现只认 `](...)`,会全量误报)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "docker")
        _project(root, "k8s")
        _mk(root, "00-索引.md", "# 索引\n\n## 计划与进度\n\n"
            "- [[10-项目/docker/!项目说明|Docker]]\n- [[10-项目/k8s/!项目说明|K8s]]\n")
        got = P.check_roadmap()
        assert not [f for f in got if "未进路线" in f.detail or "未列出" in f.detail], got


def test_a7_unlisted_projects_single_summary_finding():
    """M3:一个项目都没列出 → 只发一条汇总提示,不逐项目刷「未进路线」。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        for name in ("a", "b", "c"):
            _project(root, name)
        _mk(root, "00-索引.md", "# 索引\n\n## 计划与进度\n")
        got = P.check_roadmap()
        assert len(got) == 1, got
        assert "未列出任何项目(3 个)" in got[0].detail and "小节为空" in got[0].detail, got


def test_a7_roadmap_heading_must_be_h2():
    """路线小节标题须是行首二级:`### 计划与进度` 不算,带注解的旧标题仍算。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        _mk(root, "00-索引.md", "# 索引\n\n### 计划与进度\n\n(待补)\n")
        assert P.roadmap_section("### 计划与进度\nx\n") == ""
        assert P.roadmap_section("## 学习路线(按序;与 10-项目一处对应)\nx\n") != ""
        got = P.check_roadmap()
        assert len(got) == 1 and "缺行首二级标题" in got[0].detail, got


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


def test_a9_root_summary_project_count_checked():
    """M1:「项目 M 个」写错必须报,整个字段缺失也要报(旧实现只校验 N,M 完全不看)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "git")
        _mk(root, "00-索引.md", "# 索引\n\n> 全库知识 1 篇 · 项目 3 个\n")
        got = P.check_index_stats()
        assert any("项目 3 个与盘上项目 1" in f.detail for f in got), got
        _mk(root, "00-索引.md", "# 索引\n\n> 全库知识 1 篇\n")
        got = P.check_index_stats()
        assert any("缺「项目 M 个」" in f.detail for f in got), got


def test_a9_root_summary_ok():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "git")
        _mk(root, "00-索引.md", "# 索引\n\n> 全库知识 1 篇 · 项目 1 个\n")
        assert not P.check_index_stats(), P.check_index_stats()


def test_new_structure_end_to_end():
    """M2:真库尚无新结构,在此构造全套跑通 A7/A9,并把根汇总行的 M 改错以证明新路径非空跑。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md", "---\ntype: project\nstatus: learning\n---\n# 甲\n")
        _mk(root, "10-项目/甲/20-知识/知识甲.md",
            "---\ntype: system\nstatus: learning\n---\n# 知识甲\n")
        _mk(root, "10-项目/甲/00-索引.md",
            "# 甲\n\n> 本项目知识 1 篇 · 状态 learning · 覆盖 1/1(100%)\n\n## 计划与进度\n\n"
            "- [[知识甲]]\n")
        root_index = ("# 索引\n\n> 全库知识 1 篇 · 项目 1 个\n\n## 计划与进度\n\n"
                      "- [甲](<10-项目/甲/!项目说明.md>)\n")
        _mk(root, "00-索引.md", root_index)
        assert L.project_knowledge_dirs(root) and L.route_sources(root), "夹具没造出新结构"
        assert not P.check_roadmap(), P.check_roadmap()
        assert not P.check_index_stats(), P.check_index_stats()
        _mk(root, "00-索引.md", root_index.replace("项目 1 个", "项目 2 个"))
        got = P.check_index_stats()
        assert any("项目 2 个与盘上项目 1" in f.detail for f in got), got


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
