#!/usr/bin/env python3
"""A12 归档判据自检:四条「可归档」提示(不算错误)+ 反向「归档物须登记」错误。

夹具与 runner 自带(同 selftest_project2.py 款式);独立成文件以守住 ≤200 行。
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_archive as A

SPEC = """---
type: project
status: %s
---

# %s

- **验收:**
%s

## 任务清单

%s
%s"""


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _project(root: Path, name: str, status: str = "done",
             acceptance: str = "- [x] 达标", tasks: str = "- [x] 完工",
             review: bool = True) -> Path:
    """一个项目:`!项目说明.md` 四条判据都可控。"""
    tail = "## 六、复盘 / 出口\n\n- 已复盘,套路沉淀完毕\n" if review else "## 五、踩坑记录\n\n- 无\n"
    return _mk(root, "10-项目/%s/!项目说明.md" % name,
               SPEC % (status, name, acceptance, tasks, tail))


def test_ready_all_four_conditions_is_hint_not_error():
    """四条全满足且未搬走 → 提示「可归档:X」,且 check_archive_ready() 不得报错。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        assert A.archive_ready(root / "10-项目/甲") is True
        hints = A.archive_hints()
        assert any(h.strip() == "可归档:甲" for h in hints), hints
        assert not A.check_archive_ready(), A.check_archive_ready()  # 提示不是错误
        assert len(A.archive_hints(verbose=False)) == 1, A.archive_hints(verbose=False)


def test_status_not_done_no_hint():
    """① status 非 done(即便其余三条全满足)→ 无提示。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", status="learning")
        assert A.archive_ready(root / "10-项目/甲") is False
        assert A.archive_hints() == [], A.archive_hints()


def test_unchecked_item_in_acceptance_no_hint():
    """② 验收段里有未勾选项 → 无提示。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", acceptance="- [x] 好\n- [ ] 还没做")
        assert A.archive_hints() == [], A.archive_hints()


def test_no_review_section_no_hint():
    """③ 无「复盘」小节 → 无提示。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", review=False)
        assert A.archive_hints() == [], A.archive_hints()


def test_unchecked_item_in_tasklist_no_hint():
    """④ 任务清单段里有未勾选项 → 无提示。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", tasks="- [x] 阶段一\n- [ ] 阶段二")
        assert A.archive_hints() == [], A.archive_hints()


def test_unchecked_in_code_fence_is_ignored():
    """代码示例里的 `- [ ]` 不该拦住归档(先 strip_code 再扫判据)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", acceptance="- [x] 达标\n\n```text\n- [ ] 示例里的框\n```")
        assert A.archive_hints(), A.archive_hints()


def test_ordered_list_bold_label_is_a_section():
    """`1. **验收:**` 这种有序列表粗体标签也认作小节(不限 `-`)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "10-项目/甲/!项目说明.md",
            "---\ntype: project\nstatus: done\n---\n\n# 甲\n\n1. **验收:**\n\n"
            "   - [x] 达标\n\n## 任务清单\n\n- [x] 完工\n\n## 复盘\n\n- 已复盘\n")
        assert A.archive_hints(), A.archive_hints()


def test_unchecked_item_in_tasklist_subheading_no_hint():
    """④ 的层级口径:未勾选项写在 `### 阶段二` 子标题下,仍算任务清单段内。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲", tasks="- [x] 阶段一\n\n### 阶段二\n\n- [ ] 还没做")
        assert A.archive_hints() == [], A.archive_hints()


def test_archived_project_must_be_registered():
    """反向:40-归档 下的项目没在根 00-索引.md 留一行登记 → A12 错误。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "甲")
        _mk(root, "10-项目/乙/!项目说明.md", "---\ntype: project\nstatus: done\n---\n# 乙\n")
        _mk(root, "40-归档/甲-2026Q1/!项目说明.md", "---\ntype: project\nstatus: done\n---\n# 甲\n")
        _mk(root, "00-索引.md", "# 索引\n\n## 计划与进度\n\n- [[10-项目/乙/!项目说明|乙]]\n")
        got = A.check_archive_ready()
        assert [f.stage for f in got] == ["A12"], got
        assert "甲-2026Q1" in got[0].detail and "未在根 00-索引.md 登记" in got[0].detail, got


def test_archived_project_registered_is_clean():
    """反向:登记后(含去掉日期后缀的简称写法)不再报错。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "40-归档/甲-2026Q1/!项目说明.md", "---\ntype: project\nstatus: done\n---\n# 甲\n")
        _mk(root, "00-索引.md", "# 索引\n\n## 计划与进度\n\n- [甲](../../40-归档/甲-2026Q1/!项目说明.md)\n")
        assert not A.check_archive_ready(), A.check_archive_ready()


def test_archived_project_missing_root_index():
    """反向:根索引整个缺失时也算未登记(提示文案仍指向根 00-索引.md)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _mk(root, "40-归档/甲/!项目说明.md", "---\ntype: project\nstatus: done\n---\n# 甲\n")
        got = A.check_archive_ready()
        assert len(got) == 1 and "未在根 00-索引.md 登记" in got[0].detail, got


def test_real_vault_shape_stays_silent():
    """真库此刻的形状:0 个项目 done、40-归档 只有非项目文件 → 0 错误 0 提示(不得误报)。"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        L.VAULT_ROOT = root
        _project(root, "2026Q4-掌握Docker", status="learning",
                 acceptance="- [ ] 还没达标", tasks="- [ ] 阶段一")
        _mk(root, "40-归档/CSDN文章/开机软件0延后启动设置.md",
            "---\ntype: note\nstatus: done\n---\n# 开机软件\n")
        assert A.check_archive_ready() == [], A.check_archive_ready()
        assert A.archive_hints() == [], A.archive_hints()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
