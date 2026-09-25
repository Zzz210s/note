#!/usr/bin/env python3
"""A13 双向链接:项目索引 ↔ 项目知识双向可达,知识笔记必须写明来源项目。

一、反向(本文件的判据主体)。`10-项目/<项目>/20-知识/**/*.md` 每篇都必须声明自己的
来源项目,两种写法满足其一即可:
  ① frontmatter 里有一条指向本项目 `!项目说明.md` 的链接 —— 惯例
     `related: "[[<项目名>/!项目说明|项目]]"`。wikilink 认 `<名>/!项目说明` 的路径后缀
     (`[[10-项目/甲/!项目说明|甲]]` 同源),markdown 链接按笔记所在目录解析(与 A2 的
     路径后缀口径一致,因为本库有 18 个同名 `!项目说明.md`,只认裸名会张冠李戴)。
  ② 正文首段写明「来源:本项目」。首段 = frontmatter 之后、笔记标题(H1)之后的第一段连续
     正文;标题之后另起小节(`## 背景`)里的字样不算,`**来源:本项目**` / `> 来源:本项目`
     这类标记剥掉再认。先 `L.strip_code()` 抹掉代码,示例里的字样不算声明。

  豁免(只免反向要求):`!名词解释` / `!系统与工具` 两个容器(`L.is_container()`)没有时间盒,
  没有「本项目」可指;`20-知识/` 所在目录连 `!项目说明.md` 都没有的(真库 `!问题追踪`)同理 ——
  这类目录索要来源只会得到假阳性,其索引/归属由 A4 与索引一致性检查守。

二、正向(与 A1/A4 的分工,本文件不重复实现)。「项目索引里指向 `20-知识/` 的链接目标必须
存在」由 **A1**(markdown 链接)/ **A2**(wikilink)守;「知识必须被项目索引登记」由 **A4** 守。
A13 只补 A4 补不了的那一半:笔记已进 `20-知识/`、项目 `00-索引.md` 却还没建时,双向可达的
正向边根本不存在,无从校验 —— 每个有笔记的项目报一条(计划 Task 7 Step 4 的验收正是读这个数,
Task 8 生成索引后自然消失)。空 `20-知识/`(只有 .gitkeep)不报:没有笔记就没有可达性可言,
索引缺失由 A4 归因,避免同因双报。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

INSTRUCTION = "!项目说明.md"
# `!项目说明` 不带后缀的写法也认(Obsidian 双链惯例省略 .md)
SPEC_NAMES = (INSTRUCTION, "!项目说明")
SOURCE_RE = re.compile(r"来源\s*[:：]?\s*本项目")
HEADING = re.compile(r"^#{1,6}[ \t]")


def _frontmatter_block(text: str) -> str:
    """frontmatter 原文(含链接行);无 frontmatter 则空串。"""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def _body(text: str) -> str:
    """frontmatter 之后的正文;无 frontmatter 则全文。"""
    end = text.find("\n---", 3) if text.startswith("---") else -1
    return text if end == -1 else text[end + 4:]


def _first_paragraph(text: str) -> str:
    """笔记标题之后的第一段正文(跳过前导空行与 H1;碰到下一个标题即结束)。"""
    out: list[str] = []
    title_seen = False
    for line in L.strip_code(_body(text)).splitlines():
        if HEADING.match(line):
            if out or title_seen:
                break
            title_seen = True
            continue
        if not line.strip():
            if out:
                break
            continue
        out.append(line)
    return "\n".join(out)


def _says_source(text: str) -> bool:
    clean = _first_paragraph(text).replace("*", "").replace("`", "").replace(">", "")
    return bool(SOURCE_RE.search(clean))


def _points_to_spec(target: str, note: Path, spec: Path, project: str) -> bool:
    """链接目标是否指向本项目 `!项目说明.md`(路径后缀 + 按笔记目录解析两路兜底)。

    后缀两路都认(Obsidian 两种写法等价):`[[甲/!项目说明|甲]]` 与 `[[甲/!项目说明.md|甲]]`,
    比 stem 前先统一去掉 `.md`,否则「带后缀的写法」永远匹配不上带后缀的 tail。
    """
    core = target.split("|")[0].split("#")[0].strip().lstrip("<").rstrip(">")
    if not core or Path(core).name not in SPEC_NAMES:
        return False
    stem = core[:-3] if core.endswith(".md") else core
    tails = tuple("%s/%s" % (project, n) for n in SPEC_NAMES)
    if any(stem == t or stem.endswith("/" + t) for t in tails):
        return True
    try:                                        # 相对路径写法:按笔记目录解析(缺后缀补 .md)
        cand = note.parent / (core if core.endswith(".md") else core + ".md")
        return cand.resolve() == spec.resolve()
    except OSError:
        return False


def _spec_of(note: Path) -> Path:
    """笔记所属项目根的 `!项目说明.md`:取最近一个含该文件的祖先目录(支持 20-知识/ 嵌套)。"""
    for d in note.parents:
        if (d / INSTRUCTION).is_file():
            return d / INSTRUCTION
    return note.parents[1] / INSTRUCTION       # 20-知识/x.md 的 parents[1] = 项目根


def declares_project(note: Path, text: str, project: str) -> bool:
    """这篇笔记是否写明了来源项目(判据见模块 docstring 一、① ②)。"""
    spec = _spec_of(note)
    fm = _frontmatter_block(text)
    links = [t for _, t in L.extract_wikilinks(fm)] + [t for _, t in L.extract_links(fm)]
    if any(_points_to_spec(t, note, spec, project) for t in links):
        return True
    return _says_source(text)


def check_project_backlinks() -> list[L.Finding]:
    """A13:每个项目的 `20-知识/` 与 `00-索引.md` 必须双向可达(判据见模块 docstring)。"""
    out: list[L.Finding] = []
    for name, kd in L.project_knowledge_dirs(L.VAULT_ROOT):
        files = sorted(kd.rglob("*.md"))
        if not files:
            continue                            # 只有 .gitkeep:无笔记可判(见 docstring 二)
        proj_rel = L.rel_path(kd.parent)
        spec = kd.parent / INSTRUCTION
        index = kd.parent / L.PROJECT_INDEX
        if not index.exists():
            out.append(L.Finding("A13", L.rel_path(index), 0,
                                 "项目索引尚未建立,20-知识 的双向可达无法校验"))
        if L.is_container(proj_rel) or not spec.is_file():
            continue                            # 容器无时间盒 / 非项目目录无「本项目」可指
        out.extend(L.Finding("A13", L.rel_path(p), 0,
                             "缺来源项目声明(frontmatter 指向 `[[%s/%s|…]]`,或正文首段写「来源:本项目」)"
                             % (name, INSTRUCTION))
                   for p in files if not declares_project(p, L.read_text(p), name))
    return out
