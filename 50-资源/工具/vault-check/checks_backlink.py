#!/usr/bin/env python3
"""A13 双向链接的反向边:项目知识笔记必须写明自己的来源项目。

一、反向(本文件的判据主体)。`10-项目/<项目>/20-知识/**/*.md` 每篇都必须声明自己的
来源项目,两种写法满足其一即可:
  ① frontmatter 里有一条指向本项目 `!项目说明.md` 的链接 —— 惯例
     `related: "[[<项目名>/!项目说明|项目]]"`。wikilink 认 `<名>/!项目说明` 的路径后缀
     (`[[10-项目/甲/!项目说明|甲]]` 同源),markdown 链接按笔记所在目录解析(与 A2 的
     路径后缀口径一致,因为本库有 18 个同名 `!项目说明.md`,只认裸名会张冠李戴)。
  ② 正文首段**开头**写明「来源:本项目」。首段 = frontmatter 之后第一个标题之前的那段,或 H1
     之后到下一个标题之间的第一段连续正文;碰到任何后续标题即结束,`## 背景` 里的字样不算。
     笔记第一个结构就是二级标题时没有首段,其正文一律不算声明。声明必须是行首的显式写法
     (`来源:本项目` / `来源:本项目(…)`),`**来源:本项目**` / `> 来源:本项目` 这类前导装饰剥掉
     再认;夹在叙述句里的字样不算。先 `L.strip_code()` 抹掉代码,示例里的字样不算声明。

  豁免(只免反向要求):`!名词解释` / `!系统与工具` 两个容器(`L.is_container()`)没有时间盒,
  没有「本项目」可指;`20-知识/` 所在目录连 `!项目说明.md` 都没有的(真库 `!问题追踪`)同理 ——
  这类目录索要来源只会得到假阳性,其索引/归属由 A4 与索引一致性检查守。

二、正向(与 A1/A2/A4 的分工,本文件不重复实现)。「项目索引里指向 `20-知识/` 的链接目标必须
存在」由 **A1**(markdown 链接)/ **A2**(wikilink)守;「知识必须被项目索引登记」由 **A4** 守。
项目 `00-索引.md` 本身是否存在同样归 **A4**(它报「项目索引缺失」,见 `check_moc_coverage`)——
A13 不再报同一条,同因单报,口径与 `checks_project.py` 里注释「缺索引由 A4 报,A9 不重复」一致。于是 A13 是纯反向检查:
每篇知识笔记是否写明来源项目。空 `20-知识/`(只有 .gitkeep)不报:没有笔记就没有可判的反向边。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

INSTRUCTION = "!项目说明.md"
# Wikilink 惯例省略 `.md`,判据统一按无后缀主干比(`!项目说明.md` 先去后缀再进比较)
SPEC_STEM = "!项目说明"
# 只认显式声明:冒号必填(`来源:本项目` / `来源:本项目(真库)`),匹配限定在首行行首。旧版允许
# 省略冒号且段内任意位置命中,叙述句(「正文提到来源:本项目 这个词」)会被误认成声明。
SOURCE_RE = re.compile(r"^来源\s*[:：]\s*本项目")
SOURCE_DECOR = re.compile(r"^[>*`\s-]+")   # 行首装饰(`> ` / `**` / `- `)剥掉后再匹配
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
    """笔记的「首段」:第一个标题之前的那段,或 H1 之后到下一个标题之间的第一段连续正文。

    笔记第一个结构就是二级及以下标题时返回空 —— 那种写法没有首段,标题下的正文不算
    (否则 `## 背景` 里的一句话会被误当首段声明)。
    """
    out: list[str] = []
    h1_seen = False
    for line in L.strip_code(_body(text)).splitlines():
        if HEADING.match(line):
            if out:
                break                       # 段落后遇标题:首段到此结束
            if h1_seen:
                break                       # H1 之后又来标题:其间没有正文段落
            if len(line) - len(line.lstrip("#")) == 1:
                h1_seen = True
                continue
            return ""                       # 第一个结构是二级标题:没有首段
        if not line.strip():
            if out:
                break
            continue
        out.append(line)
    return "\n".join(out)


def _says_source(text: str) -> bool:
    """首段第一行行首是否为显式「来源:本项目」声明(判据见模块 docstring 一、②)。"""
    para = _first_paragraph(text)
    if not para:
        return False
    first = SOURCE_DECOR.sub("", para.splitlines()[0])
    return bool(SOURCE_RE.match(first))


def _points_to_spec(target: str, note: Path, spec: Path, project: str) -> bool:
    """链接目标是否指向本项目 `!项目说明.md`(路径后缀 + 按笔记目录解析两路兜底)。

    先把 `.md` 统一去掉再比裸名与路径后缀 —— 这一步是 `[[甲/!项目说明.md|…]]` 这类带后缀写法的
    唯一通路口(不先去后缀,裸名对不上 `!项目说明`、后缀也对不上无后缀的 tail)。
    """
    core = target.split("|")[0].split("#")[0].strip().lstrip("<").rstrip(">")
    stem = core[:-3] if core.endswith(".md") else core
    if not stem or Path(stem).name != SPEC_STEM:
        return False
    proj_tail = "%s/%s" % (project, SPEC_STEM)
    if stem == proj_tail or stem.endswith("/" + proj_tail):
        return True
    try:                                        # 相对路径写法:按笔记目录解析(缺后缀补 .md)
        cand = note.parent / (core if core.endswith(".md") else core + ".md")
        return cand.resolve() == spec.resolve()
    except OSError:
        return False


def _spec_of(note: Path) -> Path:
    """笔记所属项目根的 `!项目说明.md`:取最近一个含该文件的祖先目录(支持 20-知识/ 嵌套)。

    兜底 `parents[1]` 只对 `20-知识/x.md`(深度 ≥2)成立 —— 当前调用面(`check_project_backlinks`
    逐篇判,笔记都在 `20-知识/` 之下或更深)都满足这一前提,更浅的路径不可达。
    """
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
    """A13:每个项目 `20-知识/` 里的每篇知识笔记都必须写明来源项目(判据见模块 docstring)。

    正向边(索引是否存在 / 知识是否登记)不在本文件:由 A1/A2/A4 守,缺索引一律 A4 报。
    """
    out: list[L.Finding] = []
    for name, kd in L.project_knowledge_dirs(L.VAULT_ROOT):
        files = sorted(kd.rglob("*.md"))
        if not files:
            continue                            # 只有 .gitkeep:无笔记可判(见 docstring 二)
        proj_rel = L.rel_path(kd.parent)
        spec = kd.parent / INSTRUCTION
        if not (kd.parent / L.PROJECT_INDEX).exists():
            continue                            # 缺索引由 A4 报「项目索引缺失」,A13 不重复
        if L.is_container(proj_rel) or not spec.is_file():
            continue                            # 容器无时间盒 / 非项目目录无「本项目」可指
        out.extend(L.Finding("A13", L.rel_path(p), 0,
                             "缺来源项目声明(frontmatter 指向 `[[%s/%s|…]]`,或正文首段开头写「来源:本项目」)"
                             % (name, INSTRUCTION))
                   for p in files if not declares_project(p, L.read_text(p), name))
    return out
