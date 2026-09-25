#!/usr/bin/env python3
"""new_project 自检:骨架素材 / 索引渲染 / 根索引登记 / 模板与脚本输出一致。

纯断言、只读(临时目录除外),不碰真库。运行:
    cd F:/0-Note/50-资源/工具/vault-check && PYTHONIOENCODING=utf-8 python -B selftest_new_project.py
"""
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import new_project as N            # noqa: E402
import new_project_lib as S        # noqa: E402
import new_project_register as G   # noqa: E402


def _fence(path: Path, heading: str) -> str:
    """取 <heading> 小节里第一个 ```markdown 围栏块的正文。"""
    body = path.read_text(encoding="utf-8").split(heading, 1)[1]
    body = body.split("```markdown", 1)[1].split("```", 1)[0]
    return body.strip("\n") + "\n"


def test_template_matches_renderer():
    """「空骨架」与脚本渲染逐字一致:改格式只能改渲染器,别只手改模板(否则两处漂移)。"""
    tpl = _fence(S.TEMPLATE_DIR / "00-索引模板.md", "## 空骨架").replace("项目名", "甲项目")
    assert tpl == S.render_index_planned("甲项目", True), "模板空骨架与 render_project 输出不一致"


def test_instruction_from_template():
    """`!项目说明.md`:5 个 frontmatter 字段(A5 上限 8)+ 模板四节 + `--goal` 落到「目标」。"""
    text = S.instruction_text("甲项目", "把测试跑通")
    assert text.startswith("---\ntype: project\n"), text[:40]
    assert 'related: "[[甲项目/00-索引|本项目索引]]"' in text      # 不带 .md:A2 按路径后缀解析
    for sec in ("## 项目封面", "## 任务清单", "## 踩坑记录", "## 复盘 / 出口"):
        assert sec in text, sec
    assert "- **目标:** 把测试跑通" in text
    assert len(re.findall(r"^[a-z_]+:", text.split("---")[1], re.M)) == 5


def test_teach_files_cover_a11_sections():
    """A11 硬要求:MISSION 四节 + RESOURCES 的 Knowledge / Gaps,缺一即红。"""
    files = S.teach_files("甲项目")
    assert set(files) == {"MISSION.md", "RESOURCES.md", "NOTES.md"}, set(files)
    for sec in ("## Why", "## Success looks like", "## Constraints", "## Out of scope"):
        assert sec in files["MISSION.md"], sec
    for sec in ("## Knowledge", "## Gaps"):
        assert sec in files["RESOURCES.md"], sec


def test_stats_line_in_first_eight_lines():
    """A9 只读索引页前 8 行:两种分支(有说明 / 无说明)的统计行都得落进去。"""
    for spec in (True, False):
        head = S.render_index_planned("甲项目", spec).splitlines()[:8]
        assert any(l.startswith("> 本项目知识 0 篇") for l in head), (spec, head)


def test_index_branch_follows_type():
    """学习型走「有说明」分支(入口行),常驻 / 通用走容器措辞;dry-run 与落盘同源。"""
    assert "**入口:**" in S.render_index_planned("甲项目", True)
    assert "**入口:**" not in S.render_index_planned("甲容器", False)


def test_template_link_replaces_placeholder():
    """`--template` 时「模板」块的占位行换成真实链接(A1 可解析),占位行消失。"""
    idx = S.link_template(S.render_index_planned("甲项目", True), "甲项目", "周计划")
    assert "- [`90-模板/甲项目-周计划模板.md`](../../90-模板/甲项目-周计划模板.md)" in idx
    assert S.NO_TEMPLATE not in idx


def test_plan_paths_per_type():
    """生成物清单:学习带说明与 teach 三件,常驻不带;三类都建知识区 / 原料区 / 索引;幂等。"""
    plan = {N.rel(p): c for p, c in N.plan_new("甲项目", "学习", "目标", None)}
    assert "10-项目/甲项目/!项目说明.md" in plan
    assert {"10-项目/甲项目/MISSION.md", "10-项目/甲项目/RESOURCES.md",
            "10-项目/甲项目/NOTES.md"} <= set(plan)
    assert "10-项目/甲项目/20-知识/.gitkeep" in plan and "50-资源/甲项目" in plan
    assert "10-项目/甲项目/00-索引.md" in plan
    resident = {N.rel(p) for p, _ in N.plan_new("甲容器", "常驻", None, None)}
    assert "10-项目/甲容器/!项目说明.md" not in resident
    assert {"10-项目/甲容器/00-索引.md", "10-项目/甲容器/20-知识/.gitkeep"} <= resident
    tpl = {N.rel(p) for p, _ in N.plan_new("甲项目", "通用", None, "周计划")}
    assert "90-模板/甲项目-周计划模板.md" in tpl
    assert N.plan_new("甲项目", "学习", "目标", None) == N.plan_new("甲项目", "学习", "目标", None)


def test_register_row_sorted_and_idempotent():
    """根索引登记:清单行按目录名排序插入、重复登记原样返回、汇总行改成实测值。"""
    text = ("# 索引\n\n> 全库知识 1 篇 · 项目 1 个\n\n## 计划与进度\n\n- [ ] [甲1](<a>)\n\n"
            "## 项目清单\n\n| 目录 | 类型 | 状态 | 知识 | 入口 |\n| --- | --- | --- | --- | --- |\n"
            "| 甲1 | 项目 | todo | 0 | x |\n| 甲3 | 项目 | todo | 0 | x |\n")
    row = "| 甲2 | 项目 | todo | 0 | y |"
    got = G.add_project_row(text, "甲2", row)
    assert G.listed_names(got) == ["甲1", "甲2", "甲3"], G.listed_names(got)
    assert G.add_project_row(got, "甲2", row) == got, "重复登记应原样返回"
    with_plan = G.add_plan_line(got, "甲2", "- [ ] [甲2](<b>)")
    assert "- [ ] [甲2](<b>)" in with_plan
    assert G.add_plan_line(with_plan, "甲2", "- [ ] [甲2](<b>)") == with_plan, "路线行重复插"
    assert "> 全库知识 3 篇 · 项目 2 个" in G.sync_summary(got, 3, 2)


def test_vault_counts_matches_a9():
    """汇总计数与 A9 同口径:知识 = 各 `20-知识/` 的 .md 之和,项目 = 含 `!项目说明.md` 的目录数。"""
    tmp = Path(tempfile.mkdtemp(prefix="np-selftest-"))
    try:
        (tmp / "10-项目/甲/20-知识").mkdir(parents=True)
        (tmp / "10-项目/甲/20-知识/x.md").write_text("x", encoding="utf-8")
        (tmp / "10-项目/甲/!项目说明.md").write_text("---\nstatus: todo\n---\n", encoding="utf-8")
        (tmp / "10-项目/甲/20-知识/子").mkdir()
        (tmp / "10-项目/甲/20-知识/子/y.md").write_text("y", encoding="utf-8")
        (tmp / "10-项目/乙/20-知识").mkdir(parents=True)      # 有知识区、无说明(收集区)
        assert G.vault_counts(tmp) == (2, 1), G.vault_counts(tmp)
        assert G.vault_counts(tmp / "不存在") == (0, 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print("PASS=%d FAIL=0" % len(fns))
