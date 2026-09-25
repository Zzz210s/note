#!/usr/bin/env python3
"""0-Note 巡检扩展:A11 教学工作区完整性(teach 技能的状态层)。

2026-09-24 起,`10-项目/` 下每个学习项目都是一个 `teach` 教学工作区,状态层至少要有:

- `MISSION.md`    为什么学 / 成功长什么样 / 约束 / 不做什么
- `RESOURCES.md`  可信资源清单(Knowledge / Wisdom / Gaps)

这两份文件按技能协议用英文名,且**豁免** A3 孤篇、A5/A6 元数据、A7 项目产出计数
(见 `vault_lib.is_teach_scaffold`)—— 它们是技能状态,不是库内笔记。缺了就没人守,
所以单独用 A11 兜:缺文件、或文件被写成空壳(缺章节)都报。

`GLOSSARY.md` / `lessons/` / `reference/` / `assets/` / `learning-records/` 按技能要求
**按需创建**(术语表只在用户真的掌握某个词之后才加),所以 A11 不要求它们存在。

2026-09-25 起补两条:

1. **课必须在目录页上登记**。学习项目的 `00-索引.md` 要有 `## 课程` 块(列出课程地图 /
   每节课 / 速查卡)——否则课只躺在 `lessons/` 里,从目录页看不出来。项目「没有
   `00-索引.md`」这一种情况归 A4(项目索引缺失),本检查不重复报。
2. **课件引用的本地文件必须可达**。`10-项目/**/*.html` 里的本地 `href`/`src`(含共享
   课件样式 `90-模板/teach-assets/lesson.css` / `quiz.js`)解析后必须存在。样本被挪走时
   `.md` 链接检查(A1)扫不到 HTML,样式会静默失效 —— 2026-09-25 搬 teach-assets 时,
   55 处引用只靠一次性脚本验过,所以补上这条常驻检查。
3. **容器 `!名词解释` 的词条必须有课**(2026-09-25 Task 14-B 起)。它是容器、没有
   `!项目说明.md`,所以前两条都碰不到它 —— 结果是「有名词笔记但没课」没人守。现在
   `!名词解释/20-知识/*.md` 每一篇都必须在 `lessons/` 里有一节对应课程(两边文件名主干
   互相包含即算对应),且那节课必须在该容器 `00-索引.md` 的 `## 课程` 块里出现。
   另一个容器 `!系统与工具` 目前不是教学工作区(没有 `lessons/`),故意不纳入管辖。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

# 每个文件必须出现的章节标题(空壳防线:文件在、内容是占位,也算没建)
REQUIRED = {
    "MISSION.md": ("## Why", "## Success looks like", "## Constraints", "## Out of scope"),
    "RESOURCES.md": ("## Knowledge", "## Gaps"),
}

# 课程必须在项目索引页上登记(缺索引页归 A4,这里只管「有索引页但没登记课程」)。
# 行锚判定:`## 课程安排` 或代码块里的同名文字都不算(子串判定会放过它们)。
COURSE_SECTION = "## 课程"
COURSE_SECTION_RE = re.compile(r"^## 课程\s*$", re.M)

# 容器 `!名词解释`:是 teach 教学工作区(有 lessons/),但没有 `!项目说明.md`,
# 所以走不了上面的循环,得单独守「每篇词条都要有课、课要在索引上登记」。
GLOSSARY = "10-项目/!名词解释"
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


def check_glossary_lessons() -> list[L.Finding]:
    """A11:容器 `!名词解释` 的每篇词条都要有对应课程,且该课在容器索引上登记。

    对应关系按「主干互相包含」判:词条 `测试夹具是什么` 与课件 `0005-测试夹具` 算一对
    (课件名往往缩短,所以两个方向都要认)。容器缺 `00-索引.md` 时只报「缺课」,
    索引缺失本身归 A4。
    """
    out: list[L.Finding] = []
    base = L.VAULT_ROOT / GLOSSARY
    kd = base / L.KNOWLEDGE_DIR
    if not kd.is_dir():
        return out
    lessons = (sorted((base / "lessons").glob("*.html"))
               if (base / "lessons").is_dir() else [])
    cores = [(f, _core(f.stem)) for f in lessons]
    index = base / L.PROJECT_INDEX
    section = _course_section(L.read_text(index)) if index.exists() else ""
    for note in sorted(kd.glob("*.md")):
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
    root = L.VAULT_ROOT / "10-项目"
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
    """A11:每个学习项目(有 `!项目说明.md` 的项目目录)必须是一个可用的教学工作区。"""
    out: list[L.Finding] = []
    root = L.VAULT_ROOT / "10-项目"
    if not root.exists():
        return out
    for proj in sorted(p for p in root.iterdir() if p.is_dir()):
        if not (proj / "!项目说明.md").exists():
            continue          # 追踪区等非学习项目(无项目说明)不在管辖范围
        rel_proj = L.rel_path(proj)
        for name, sections in REQUIRED.items():
            f = proj / name
            if not f.exists():
                out.append(L.Finding("A11", rel_proj, 0, "缺 %s(教学工作区状态层)" % name))
                continue
            text = L.read_text(f)
            missing = [s for s in sections if s not in text]
            if missing:
                out.append(L.Finding("A11", L.rel_path(f), 0,
                                     "缺章节 %s(疑似空壳)" % " / ".join(missing)))
        idx = proj / L.PROJECT_INDEX
        if idx.exists() and not COURSE_SECTION_RE.search(L.strip_code(L.read_text(idx))):
            out.append(L.Finding("A11", L.rel_path(idx), 0,
                                 "缺「%s」块(课在 lessons/ 与 reference/ 里却未在目录页登记)"
                                 % COURSE_SECTION))
    out.extend(check_course_assets())
    out.extend(check_glossary_lessons())
    return out
