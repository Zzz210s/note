#!/usr/bin/env python3
"""0-Note 巡检扩展:A11 教学工作区完整性(teach 技能的状态层)。

2026-09-24 起,`10-项目/` 下的教学工作区都要有状态层三件套:

- `MISSION.md`    为什么学 / 成功长什么样 / 约束 / 不做什么
- `RESOURCES.md`  可信资源清单(Knowledge / Wisdom / Gaps)
- `NOTES.md`      教学偏好 / 本项目专属 / 环境就绪状态

它们按技能协议用英文名,且**豁免** A3 孤篇、A5/A6 元数据、A7 项目产出计数
(见 `vault_lib.is_teach_scaffold`)—— 是技能状态,不是库内笔记。缺了就没人守,
所以单独用 A11 兜:缺文件、或文件被写成空壳(缺章节)都报。

「教学工作区」的判据(2026-09-25):目录下有 `lessons/`、或已经建了三件套中的任一份、
或带 `!项目说明.md`。先看"建了没有"再看"该不该建",所以删文件逃不掉管辖 —— 只要还剩
一份状态层(或 `lessons/`、或项目说明),三件套就都要在。容器(`!名词解释`)与学习项目
同一套判据,不存在"容器三件套无人守"的缺口。

`GLOSSARY.md` / `lessons/` / `reference/` / `assets/` / `learning-records/` 按技能要求
**按需创建**(术语表只在用户真的掌握某个词之后才加),所以 A11 不要求它们存在。

2026-09-25 起补三条:

1. **课必须在目录页上登记**。工作区的 `00-索引.md` 要有 `## 课程` 块(列出课程地图 /
   每节课 / 速查卡)——否则课只躺在 `lessons/` 里,从目录页看不出来。工作区「没有
   `00-索引.md`」这一种情况归 A4(项目索引缺失),本检查不重复报。
2. **课件引用的本地文件必须可达**。`10-项目/**/*.html` 里的本地 `href`/`src`(含共享
   课件样式 `90-模板/teach-assets/lesson.css` / `quiz.js`)解析后必须存在。样本被挪走时
   `.md` 链接检查(A1)扫不到 HTML,样式会静默失效。
3. **容器型工作区的词条必须有课**。有 `lessons/` 但没有 `!项目说明.md` 的容器(如
   `!名词解释`)走不到学习项目的循环,得单独守:`20-知识/**/*.md` 每一篇都必须在
   `lessons/` 里有一节对应课程(两边文件名主干互相包含即算对应),且那节课要登记在
   容器索引的 `## 课程` 块里。`!系统与工具` / `!问题追踪` 目前没有 `lessons/`,
   不是工作区,不管辖。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

# 每个工作区必须有的文件与章节标题(空壳防线:文件在、内容是占位,也算没建)
REQUIRED = {
    "MISSION.md": ("## Why", "## Success looks like", "## Constraints", "## Out of scope"),
    "RESOURCES.md": ("## Knowledge", "## Gaps"),
    "NOTES.md": ("## 教学偏好",),
}

# 课程必须在工作区索引页上登记(缺索引页归 A4,这里只管「有索引页但没登记课程」)。
# 行锚判定:`## 课程安排` 或代码块里的同名文字都不算(子串判定会放过它们)。
COURSE_SECTION = "## 课程"
COURSE_SECTION_RE = re.compile(r"^## 课程\s*$", re.M)

# 课件名的编号前缀(`0001-...`);去掉它才好和词条主干比对。
LESSON_NUM_RE = re.compile(r"^[0-9]+[-_.]")


def _core(name: str) -> str:
    """文件名主干:去掉 `NNNN-` 编号前缀,再小写化(两边都比主干,不管大小写)。"""
    return LESSON_NUM_RE.sub("", name).strip().lower()


def _course_section(text: str) -> str:
    """`## 课程` 块的正文(到下一个 `##` 标题或文末);先抹白代码块,免得抄示例过关。"""
    stripped = L.strip_code(text)
    m = COURSE_SECTION_RE.search(stripped)
    if not m:
        return ""
    rest = stripped[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def _project_dirs() -> list[Path]:
    """`10-项目/` 的直属子目录。"""
    base = L.VAULT_ROOT / L.PROJECT_ROOT
    return [p for p in sorted(base.iterdir()) if p.is_dir()] if base.is_dir() else []


def _work_areas() -> list[Path]:
    """教学工作区:带 `!项目说明.md`、或带 `lessons/`、或已建三件套中任一份的目录。

    先看"建了没有"再看"该不该建",所以删掉一份状态层文件逃不掉管辖 —— 只要还剩
    `lessons/` 或另一份,整条三件套就都要在。
    """
    return [p for p in _project_dirs()
            if (p / "!项目说明.md").exists() or (p / "lessons").is_dir()
            or any((p / n).exists() for n in REQUIRED)]


def _container_workspaces() -> list[Path]:
    """容器型工作区:有 `lessons/` 但没有 `!项目说明.md` 的 `10-项目/<目录>`。"""
    return [p for p in _project_dirs()
            if (p / "lessons").is_dir() and not (p / "!项目说明.md").exists()]


def _scaffold_findings(work: Path) -> list[L.Finding]:
    """三件套:缺文件、或文件缺必需章节(空壳)都报。"""
    out: list[L.Finding] = []
    for name, sections in REQUIRED.items():
        f = work / name
        if not f.exists():
            out.append(L.Finding("A11", L.rel_path(work), 0,
                                 "缺 %s(教学工作区状态层)" % name))
            continue
        missing = [s for s in sections if s not in L.read_text(f)]
        if missing:
            out.append(L.Finding("A11", L.rel_path(f), 0,
                                 "缺章节 %s(疑似空壳)" % " / ".join(missing)))
    return out


def check_glossary_lessons() -> list[L.Finding]:
    """A11:容器型工作区的每篇词条都要有对应课程,且该课在容器索引上登记。

    对应关系按「主干互相包含」判:词条 `测试夹具是什么` 与课件 `0005-测试夹具` 算一对
    (课件名往往缩短,所以两个方向都要认)。容器缺 `00-索引.md` 时只报「缺课」,
    索引缺失本身归 A4。
    """
    out: list[L.Finding] = []
    for base in _container_workspaces():
        kd = base / L.KNOWLEDGE_DIR
        if not kd.is_dir():
            continue
        cores = [(f, _core(f.stem)) for f in sorted((base / "lessons").glob("*.html"))]
        index = base / L.PROJECT_INDEX
        section = _course_section(L.read_text(index)) if index.exists() else ""
        for note in sorted(kd.rglob("*.md")):
            core = _core(note.stem)
            hit = next((f for f, c in cores if c and core and (core in c or c in core)), None)
            if hit is None:
                out.append(L.Finding("A11", L.rel_path(note), 0,
                                     "在 lessons/ 里没有对应课程"))
            elif index.exists() and hit.name not in section:
                out.append(L.Finding("A11", L.rel_path(note), 0,
                                     "课程 %s 未在容器的「%s」块登记" % (hit.name, COURSE_SECTION)))
    return out


# 课件(HTML)里的本地引用;外链、协议相对、锚点、mailto 等跳过
HTML_REF_RE = re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""")
NON_LOCAL = ("http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:", "#", "/")


def _html_refs(html: Path) -> Iterator[tuple[int, str]]:
    """HTML 里的本地引用 → (行号, 去掉 #片段/?查询 后的相对目标)。"""
    for i, line in enumerate(L.read_text(html).splitlines(), 1):
        for m in HTML_REF_RE.finditer(line):
            target = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            if not target or target.startswith(NON_LOCAL):
                continue
            bare = target.split("#")[0].split("?")[0]
            if bare:
                yield i, bare


def check_course_assets() -> list[L.Finding]:
    """A11:课件引用的本地文件必须存在(teach-assets 一挪,样式就静默失效)。"""
    out: list[L.Finding] = []
    root = L.VAULT_ROOT / L.PROJECT_ROOT
    if not root.exists():
        return out
    for html in sorted(root.rglob("*.html")):
        if any(part in L.SKIP_DIRS for part in html.parts):
            continue
        for line, target in _html_refs(html):
            if not (html.parent / target).resolve().exists():
                out.append(L.Finding("A11", L.rel_path(html), line,
                                     "课件引用的文件不存在:%s" % target))
    return out


def check_teach_workspace() -> list[L.Finding]:
    """A11:每个教学工作区(学习项目与容器)都要可用:三件套齐全 + 课在目录页登记。"""
    out: list[L.Finding] = []
    for work in _work_areas():
        out.extend(_scaffold_findings(work))
        idx = work / L.PROJECT_INDEX
        if idx.exists() and not COURSE_SECTION_RE.search(L.strip_code(L.read_text(idx))):
            out.append(L.Finding("A11", L.rel_path(idx), 0,
                                 "缺「%s」块(课在 lessons/ 与 reference/ 里却未在目录页登记)"
                                 % COURSE_SECTION))
    out.extend(check_course_assets())
    out.extend(check_glossary_lessons())
    return out