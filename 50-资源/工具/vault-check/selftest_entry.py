#!/usr/bin/env python3
"""入口端到端自检:直接调 `check_vault.main()`,验证「提示通道不进 FAIL 计数」。

A12 的「可归档」是**提示**(要人动手搬家,不是库的毛病),所以它必须走独立小节、不参与
`bad` 计数。单测 `archive_hints()` 的返回值证明不了这一点:真值只在入口那一层 ——
提示打印了、退出码仍是 0。本文件把这个链路(临时库 → main() → stdout + 退出码)跑通,
独立成文件以免 selftest_archive.py 越过 200 行上限。
"""
import contextlib
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import check_vault as C

SPEC = """---
type: project
status: done
---

# 甲

- **验收:**

- [x] 达标

## 任务清单

- [x] 完工

## 六、复盘 / 出口

- 已复盘,套路沉淀完毕
"""
MISSION = ("## Why\n\nx\n\n## Success looks like\n\nx\n\n## Constraints\n\nx\n\n"
           "## Out of scope\n\nx\n")
RESOURCES = "## Knowledge\n\nx\n\n## Gaps\n\nx\n"
INDEX = """---
type: note
status: done
---

# 索引

> 全库知识 0 篇 · 项目 1 个

## 计划与进度

- [ ] [甲](<../10-项目/甲/!项目说明.md>) · 见 [[00-索引/00-索引|根索引]]
"""


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _clean_vault(root: Path) -> None:
    """一个 A1~A11 全绿、且四条归档判据全满足的库(故 A12 只出提示)。"""
    _mk(root, "10-项目/甲/!项目说明.md", SPEC)
    _mk(root, "10-项目/甲/MISSION.md", MISSION)      # A11 要求的状态层
    _mk(root, "10-项目/甲/RESOURCES.md", RESOURCES)
    _mk(root, "00-索引/00-索引.md", INDEX)


def test_archive_hint_keeps_entry_point_passing():
    """存在「可归档」提示时,入口仍须 rc=0 / 结论 PASS(A12 review M1 守门用例)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _clean_vault(root)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = C.main(["--quiet"])
        text = buf.getvalue()
        assert "可归档项目 1 个" in text, text        # ① 提示文案出现
        assert "[A12 归档判据] 0 处" in text, text    # ② A12 的错误数为 0
        assert "结论:PASS" in text and rc == 0, (rc, text)   # ③ 入口返回码为 0


def test_archive_registration_error_fails_entry_point():
    """对照:归档项目真的漏登记时,同一入口必须报错并给出 rc=1(提示/错误两条路都不哑)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _clean_vault(root)
        _mk(root, "40-归档/丙-2026Q1/!项目说明.md",
            "---\ntype: project\nstatus: done\n---\n\n# 丙\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = C.main(["--quiet"])
        text = buf.getvalue()
        assert "[A12 归档判据] 1 处" in text, text
        assert "结论:FAIL" in text and rc == 1, (rc, text)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
