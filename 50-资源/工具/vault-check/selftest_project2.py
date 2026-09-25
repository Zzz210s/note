#!/usr/bin/env python3
"""项目口径补充自检:容器目录不得算项目数 / 项目索引里的跨项目库根 wikilink 不误报。

单独成文件是为了守住 ≤200 行(selftest_project.py 已近上限),夹具与 runner 自带。
"""
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


def test_t1_container_dir_is_not_a_project():
    """T1:没有 `!项目说明.md` 的容器目录(真库 `10-项目/!问题追踪`)不算项目。

    若 project_dirs() 退回「10-项目/ 全部子目录」,这里两个断言都会红。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "git")
        _mk(root, "10-项目/!问题追踪/问题甲.md",
            "---\ntype: log\nstatus: doing\n---\n# 问题甲\n")
        assert [p.name for p in L.project_dirs(root)] == ["git"], L.project_dirs(root)
        _mk(root, "00-索引.md", "# 索引\n\n> 全库知识 1 篇 · 项目 1 个\n")
        assert not P.check_index_stats(), P.check_index_stats()
        _mk(root, "00-索引.md", "# 索引\n\n> 全库知识 1 篇 · 项目 2 个\n")
        got = P.check_index_stats()
        assert any("项目 2 个与盘上项目 1" in f.detail for f in got), got


def test_c1_project_index_wikilink_to_other_project():
    """C1:项目索引页里指向**另一个**项目的库根相对 wikilink 不得被丢掉。

    旧实现在 `src.parent/` 先解析成 `10-项目/k8s/10-项目/docker/!项目说明`,取 parts[0]
    得到 k8s(等于来源页自身)→ 首个候选就 return → 库根候选不再尝试 → docker 被误报。
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "k8s")
        _project(root, "2026Q4-掌握Docker")
        _mk(root, "00-索引.md", "# 索引\n\n## 计划与进度\n\n- [[10-项目/k8s/!项目说明|K8s]]\n")
        _mk(root, "10-项目/k8s/00-索引.md", "# k8s 索引\n\n## 计划与进度\n\n"
            "- [[10-项目/2026Q4-掌握Docker/!项目说明|Docker]]\n")
        got = P.check_roadmap()
        assert not [f for f in got if "2026Q4-掌握Docker" in f.detail], got
        assert not [f for f in got if "未进路线" in f.detail or "未列出" in f.detail], got
        assert "2026Q4-掌握Docker" in P._listed_projects(), P._listed_projects()


def test_c1_self_link_still_not_listed():
    """C1 的反向:来源页链自己的 `!项目说明.md` 仍不算「把自身洗白」。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "k8s")
        _mk(root, "10-项目/k8s/00-索引.md", "# k8s 索引\n\n## 计划与进度\n\n"
            "- [[10-项目/k8s/!项目说明|K8s]]\n- [K8s](<./!项目说明.md>)\n")
        assert P._listed_projects() == set(), P._listed_projects()
        got = P.check_roadmap()
        assert any("未列出任何项目" in f.detail for f in got), got


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
