#!/usr/bin/env python3
"""new_project.py 的素材层:新项目各文件长什么样。

分工:`new_project.py` 管编排(该建哪些件 / 建没建过 / 怎么打印),`new_project_register.py`
管根 `00-索引.md` 的登记,本层只管文本 —— 三层各守仓库「自研代码 ≤200 行」的规矩。

索引页不另写一套:直接复用 Task 8 的 `gen_indexes_render.render_project`,统计行与五块
(计划与进度 / 原料 / 知识产出 / 模板 / 出口)跟巡检 A9 / A14 口径天然一致。
"""
from __future__ import annotations

import contextlib
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

VAULT = Path(__file__).resolve().parents[3]            # <仓库根>
TOOLS = VAULT / "50-资源" / "工具"
TEMPLATE_DIR = VAULT / "90-模板"
INSTRUCTION_TEMPLATE = TEMPLATE_DIR / "10-项目立项模板.md"
PROJECTS = "10-项目"
KNOWLEDGE = "20-知识"
RESOURCE_DIR = "50-资源"
INSTRUCTION = "!项目说明.md"
INDEX = "00-索引.md"
INDEX_STEM = "00-索引"          # 双链写法不带扩展名(A2 按路径后缀解析)

sys.path.insert(0, str(TOOLS))
import gen_indexes_lib as GL        # noqa: E402  常量(导入不触发旧 MOC 解析)
import gen_indexes_render as R      # noqa: E402  Task 8 的索引页渲染器

CONTAINERS = GL.CONTAINERS

# render_project 在「无专属模板」时写的占位行;给了 --template 就换成真实链接。
NO_TEMPLATE = "- 暂无专属模板;需要时放项目内 `90-模板/` 或全局 `90-模板/`。"


def instruction_text(name: str, goal: str | None = None, status: str = "todo") -> str:
    """`!项目说明.md`:frontmatter + 模板的「项目封面 → 复盘 / 出口」段。

    模板头部(属于哪层 / 作用 / 要点)与末尾示例段不落盘;A5 字段数上限 8,故只留 5 个。
    """
    lines = INSTRUCTION_TEMPLATE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## "))
    end = next((i for i in range(start, len(lines)) if lines[i].strip() == "---"), len(lines))
    body = lines[start:end]
    if goal:
        body = [("- **目标:** " + goal) if l.startswith("- **目标:**") else l for l in body]
    while body and not body[-1].strip():
        body.pop()
    head = ["---", "type: project", "tags: [%s]" % name, "status: %s" % status,
            "date: %s" % date.today().isoformat(),
            'related: "[[%s/%s|本项目索引]]"' % (name, INDEX_STEM), "---", "",
            "# %s" % name, "",
            "**入口:** [%s](<%s>)(计划 / 原料 / 知识 / 模板 / 出口)。" % (INDEX, INDEX), ""]
    return "\n".join(head + body) + "\n"


MISSION = """\
# Mission: %(name)s

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,
> 本文件管「为什么学」);教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

- TODO(开课前先填):这个项目要解决的真实问题是什么?**具体优于抽象** —— 写不出就先访谈用户。

## Success looks like

- TODO:一件可观察的事(做什么、做到什么程度算成)

## Constraints

- 窗口:%(window)s;时间 / 预算 / 已有承诺
- 以本机真实工作流为练习对象

## Out of scope

- TODO:明确不追的相邻话题(保护最近发展区)
"""

RESOURCES = """\
# %(name)s Resources

> 本项目教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆(A11 守这两节)。

## Knowledge

- TODO:[来源名](https://example.com) — 覆盖什么、什么时候用它;只收高信任一手来源

## Wisdom (Communities)

- (暂无)

## Gaps

- TODO:还没有可信来源的方向(这份缺口驱动后续检索)
"""

NOTES = """\
# NOTES

> 教学偏好与工作笔记。设计课程前先读这份文件。

## 教学偏好(全局,用户已确认)

- **语言与格式**:中文输出;不用 emoji;概念讲解固定三段式「为解决什么痛点而生 / 一句话定义 / 大白话注解」
- **文档风格**:结论先行、表格优先;具体胜过形容
- **笔记归属**:成品知识写进本项目 `20-知识/`(项目层只留脚手架与过程记录)
- **链接**:正文互连用 `[[双链]]`;索引用相对路径链接
- **每节课的硬要求**:一个当场可验证的小胜利 + 等长选项的测验 + 一手资源引用
- **篇幅**:代码文件 ≤200 行;`.md` 笔记不限长

## 本项目专属

- (待记:用户说过的、只针对这个项目的偏好)

## 环境就绪状态

- (待测:依赖装好没有 / 怎么验证 / 下一步命令 —— 交接给别的会话时先读这段)
"""


def teach_files(name: str, window: str = "待定") -> dict[str, str]:
    """学习型的 teach 三件(A11 要求 MISSION 四节 + RESOURCES 的 Knowledge / Gaps)。"""
    return {"MISSION.md": MISSION % {"name": name, "window": window},
            "RESOURCES.md": RESOURCES % {"name": name},
            "NOTES.md": NOTES}


def template_text(name: str, use: str) -> str:
    """项目专属模板占位:`90-模板/<项目名>-<用途>模板.md`。"""
    return ("# %s - %s模板\n\n"
            "> **属于哪层:** `10-项目/%s/` 的项目专属格式。\n"
            "> **作用:** 项目内「%s」类文档的统一格式 —— 照此写,别各自发挥。\n"
            "> **要点:** 立项目时起草,随项目演进改;不需要就删掉本文件。\n\n"
            "## 一段式样例\n\n"
            "- 用途:%s\n"
            "- 频率:按需\n\n"
            "## 小节\n\n"
            "- TODO:按真实表格 / 清单填写\n") % (name, use, name, use, use)


def link_template(text: str, name: str, use: str) -> str:
    """把索引「模板」块的占位行换成专属模板链接(写法同 render_project 的已知模板)。"""
    if NO_TEMPLATE not in text:
        raise RuntimeError("索引「模板」块的占位行没找到 —— render_project 的文案变了?")
    f = "%s-%s模板.md" % (name, use)
    return text.replace(NO_TEMPLATE, "- [`90-模板/%s`](../../90-模板/%s)" % (f, f))


@contextlib.contextmanager
def _staged_root(name: str, spec: bool):
    """临时仓库根:预置(或不预置)`!项目说明.md`,让渲染器走对应分支。"""
    tmp = Path(tempfile.mkdtemp(prefix="new-project-"))
    proj = tmp / PROJECTS / name
    proj.mkdir(parents=True, exist_ok=True)
    if spec:
        (proj / INSTRUCTION).write_text("---\ntype: project\nstatus: todo\n---\n",
                                        encoding="utf-8", newline="\n")
    saved = (R.ROOT, GL.ROOT)
    R.ROOT = GL.ROOT = tmp
    try:
        yield
    finally:
        R.ROOT, GL.ROOT = saved
        shutil.rmtree(tmp, ignore_errors=True)


def render_index(name: str) -> str:
    """按盘上现状渲染(Task 8 渲染器原样调用;已存在的知识会被自动登记一行)。"""
    return R.render_project(name, {})


def render_index_planned(name: str, spec: bool) -> str:
    """新建用:真实落盘顺序是「先写说明、再渲染索引」,这里在临时根上预演同一顺序。

    否则 dry-run(说明还没落盘)会走「无说明」分支,输出与真实落盘不一致。
    """
    with _staged_root(name, spec):
        return R.render_project(name, {})
