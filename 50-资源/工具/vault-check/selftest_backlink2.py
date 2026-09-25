#!/usr/bin/env python3
"""A13 自检(豁免与入口):容器 / 非项目目录不要求来源;A13 报错进 FAIL 计数,全绿时 rc=0。

豁免只免**反向来源**:`!名词解释` / `!系统与工具` 没有时间盒(无「本项目」可指),`20-知识/` 无
`!项目说明.md` 的目录(真库 `!问题追踪`)同理。它们的索引页仍要建 —— 与 A4 的项目口径同源。
入口用例走 `check_vault.main()`,证明 A13 真能拦住 FAIL、且 A1~A13 全绿时 rc=0。
"""
import contextlib
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import check_vault as C

KNOWLEDGE = "---\ntype: note\nstatus: learning\n---\n\n# 门\n"
INDEX = "---\ntype: note\nstatus: learning\n---\n\n# %s 索引\n\n## 知识产出\n\n- [门](<./20-知识/门.md>)\n"
SPEC = "---\ntype: project\nstatus: learning\n---\n\n# 甲\n"
MISSION = ("## Why\n\nx\n\n## Success looks like\n\nx\n\n## Constraints\n\nx\n\n"
           "## Out of scope\n\nx\n")
RESOURCES = "## Knowledge\n\nx\n\n## Gaps\n\nx\n"
NOTE = """---
type: note
status: learning
related: "[[甲/!项目说明|项目]]"
---

# x

正文。
"""
ROOT_INDEX = """---
type: note
status: learning
---

# 索引

> 全库知识 1 篇 · 项目 1 个

- [甲](<10-项目/甲/!项目说明.md>)
- [甲索引](<10-项目/甲/00-索引.md>)
"""
PROJECT_INDEX = """---
type: note
status: learning
---

# 甲 索引

> 本项目知识 1 篇 · 状态 learning · 覆盖 1/1(100%)

## 知识产出

- [x](<./20-知识/x.md>)
- [根索引](<../../00-索引.md>)
"""


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _clean_vault(root: Path) -> None:
    """A1~A13 全绿的库:一个项目(索引 + 一篇写好来源的知识)。"""
    _mk(root, "10-项目/甲/!项目说明.md", SPEC)
    _mk(root, "10-项目/甲/MISSION.md", MISSION)
    _mk(root, "10-项目/甲/RESOURCES.md", RESOURCES)
    _mk(root, "10-项目/甲/00-索引.md", PROJECT_INDEX)
    _mk(root, "10-项目/甲/20-知识/x.md", NOTE)
    _mk(root, "00-索引.md", ROOT_INDEX)


def test_container_needs_no_backlink():
    """`!名词解释/20-知识/` 的笔记没有来源声明 → 不报(容器没有时间盒)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!名词解释/20-知识/门.md", KNOWLEDGE)
        _mk(root, "10-项目/!名词解释/00-索引.md", INDEX % "!名词解释")
        assert L.is_container("10-项目/!名词解释/20-知识/门.md")
        assert C.B.check_project_backlinks() == [], C.B.check_project_backlinks()


def test_non_project_dir_needs_no_backlink():
    """有 `20-知识/` 但没有 `!项目说明.md` 的目录(真库 `!问题追踪`)没有「本项目」可指 → 不报。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!问题追踪/20-知识/记录.md", "---\ntype: log\nstatus: done\n---\n\n# 记录\n")
        _mk(root, "10-项目/!问题追踪/00-索引.md", INDEX % "!问题追踪")
        assert C.B.check_project_backlinks() == [], C.B.check_project_backlinks()


def test_container_still_needs_its_index():
    """豁免只免反向来源:容器 `20-知识/` 有笔记、索引页未建 → 仍报「项目索引尚未建立」。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/!系统与工具/20-知识/门.md", KNOWLEDGE)
        got = C.B.check_project_backlinks()
        assert len(got) == 1 and "项目索引尚未建立" in got[0].detail, got


def test_entry_point_passes_when_all_green():
    """A1~A13 全绿(含 A13 的反向声明齐备)→ 结论 PASS 且 rc=0。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _clean_vault(root)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = C.main(["--quiet"])
        text = buf.getvalue()
        assert "[A13 双向链接] 0 处" in text, text
        assert "结论:PASS" in text and rc == 0, (rc, text)


def test_entry_point_fails_when_backlink_missing():
    """对照:同一库把知识笔记的来源声明删掉 → A13 报 1 处、结论 FAIL、rc=1。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _clean_vault(root)
        _mk(root, "10-项目/甲/20-知识/x.md", "---\ntype: note\nstatus: learning\n---\n\n# x\n\n正文。\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = C.main(["--quiet"])
        text = buf.getvalue()
        assert "[A13 双向链接] 1 处" in text, text
        assert "结论:FAIL" in text and rc == 1, (rc, text)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
