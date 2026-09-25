#!/usr/bin/env python3
"""A14 索引页一致性:根索引的项目清单、项目索引的知识链接数都必须与实物一致。

判据只有两条;凡 A4/A9 已经管的缺陷,这里一律不重复报(同因单报)。

① 根 `00-索引.md` 必须列出 `10-项目/` 下的**每一个子目录**,一个目录一行 —— 项目、两个容器
   (`!名词解释` / `!系统与工具`)、以及 `!问题追踪` 这类没有 `!项目说明.md` 的目录都要有入口。
   判定口径是「某一行里出现了该目录名」(与 A12 的归档登记同为文本级,对列表/表格两种写法都
   不挑食)。根索引**不存在**时整条跳过:过渡期尚未生成,不能算库的毛病;该状态只走提示通道
   `index_hints()`(同 A12 的「可归档」提示:独立小节,不进 FAIL 计数)。
   判据集合刻意比 A7 宽:A7 的单位是「有没有一条指向 `!项目说明.md` 的路线条目」,只看
   `L.project_dirs()`(带说明的项目);本检查的单位是「根索引清单有没有这一行」,容器与追踪
   目录也算。单位不同,故不是重复报。
   与 A7 的分工(2026-09-25 修复轮):A7 已经点名「未进路线」的项目(`P.roadmap_reported()`)
   在这里**跳过** —— 路线/枢纽入口缺失归 A7 单报;本检查只做「补充发现」,报 A7 永远够不到的
   容器 / 追踪目录,以及别处已经指到、只差根索引那一行的项目。

② 每个项目 `00-索引.md` 里指向本项目 `20-知识/` 下**已存在 .md 文件**的链接数,必须等于
   `20-知识/` 的 .md 实物数:少了说明只写了名字没给链接,多了说明重复登记或链到不存在的知识。
   指向别处(说明 / 模板 / 原料 / 别的项目)的链接不参与计数。与 A4/A9 的分工(重要):
   - 项目缺 `00-索引.md` → 跳过,A4 报「项目索引缺失」;
   - 有笔记没被登记(主干没在索引全文出现)→ 跳过,A4 报「未在项目索引出现」;
   - 统计行的篇数 / 覆盖 / 状态不符 → A9 报(计划原文的 ③ 已整体归 A9),本检查不读统计行。
   于是 ② 只回答 A4 的补集:登记是否**都是文件链接**、且不重复。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L
import checks_project as P


def project_subdirs(root: Path | None = None) -> list[Path]:
    """`10-项目/` 下的全部子目录(含容器与没有 `!项目说明.md` 的追踪目录)。"""
    base = (root or L.VAULT_ROOT) / L.PROJECT_ROOT
    if not base.is_dir():
        return []
    return [p for p in sorted(base.iterdir()) if p.is_dir()]


def _listed(text: str, name: str) -> bool:
    """name 是否出现在索引的某一行里(「一个目录一行」的文本级判定,对列表/表格都不挑)。"""
    return any(name in line for line in text.splitlines())


def check_root_lists_projects() -> list[L.Finding]:
    """A14①:根索引须列出 `10-项目/` 下每一个子目录(判据见模块 docstring)。

    已归 A7 的「未进路线」项目(`P.roadmap_reported()`)跳过,同一条缺失不报两次。
    """
    index = L.VAULT_ROOT / L.PROJECT_INDEX
    if not index.is_file():
        return []                       # 过渡期:根索引尚未创建 → 跳过,只走 index_hints()
    text = L.read_text(index)
    rel = L.rel_path(index)
    skip = P.roadmap_reported()         # 路线/枢纽缺失的账记在 A7 头上
    return [L.Finding("A14", rel, 0, "根索引未列出项目 %s" % d.name)
            for d in project_subdirs() if not _listed(text, d.name) and d.name not in skip]


def unlisted_notes(kd: Path, index_text: str) -> list[Path]:
    """索引没登记的笔记:主干没在索引全文出现。

    口径必须与 A4(`check_vault.check_index_coverage` 里的 `p.stem not in idx`)一致:分工正是
    靠它划界(未登记归 A4),`selftest_index2.py` 有用例把两边锁在一起。
    """
    return [p for p in sorted(kd.rglob("*.md")) if p.stem not in index_text]


def _inside(path: Path, d: Path) -> bool:
    try:
        path.resolve().relative_to(d.resolve())
        return True
    except (OSError, ValueError):
        return False


def _is_md(p: Path) -> bool:
    return p.is_file() and p.suffix == ".md"


def knowledge_link_count(index: Path, kd: Path) -> int:
    """索引页里指向本项目 `20-知识/` 下已存在 .md 文件的链接数(同一文件链两次算两个)。

    两路都认:markdown 链接按索引页所在目录解析(与 A1 同口径),wikilink 是库根相对,故再按
    库根兜底一次;`[[知识名]]` 这种省略路径与后缀的裸写法按本项目知识主干兜底(与 A4 用主干
    判登记同一惯例)。指向别处、或指向不存在的文件,都不计数 —— 后者是 A1 的地盘。
    """
    text = L.read_text(index)
    stems = {p.stem for p in kd.rglob("*.md")}
    n = 0
    for _, target in L.extract_links(text):
        bare = target.split("#")[0].strip().lstrip("<").rstrip(">")
        if not bare or bare.startswith(("http", "mailto")):
            continue
        cand = index.parent / bare
        if _is_md(cand) and _inside(cand, kd):
            n += 1
    for _, target in L.extract_wikilinks(text):
        core = target.split("|")[0].split("#")[0].strip().lstrip("/")
        if not core:
            continue
        cands = (index.parent / core, index.parent / (core + ".md"),
                 L.VAULT_ROOT / core, L.VAULT_ROOT / (core + ".md"))
        if any(_is_md(c) and _inside(c, kd) for c in cands):
            n += 1
        elif "/" not in core:
            stem = core[:-3] if core.endswith(".md") else core
            if stem in stems:
                n += 1
    return n


def check_project_index_links() -> list[L.Finding]:
    """A14②:项目索引的知识文件链接数须等于 `20-知识/` 实物数(分工见模块 docstring)。"""
    out: list[L.Finding] = []
    for _, kd in L.project_knowledge_dirs(L.VAULT_ROOT):
        index = kd.parent / L.PROJECT_INDEX
        if not index.is_file():
            continue                    # 缺索引 → A4 报「项目索引缺失」
        files = sorted(kd.rglob("*.md"))
        if not files:
            continue                    # 空知识区(只有 .gitkeep):没有可数的实物
        text = L.read_text(index)
        if unlisted_notes(kd, text):
            continue                    # 有未登记条目 → A4 报,A14 不重复
        n = knowledge_link_count(index, kd)
        if n != len(files):
            out.append(L.Finding("A14", L.rel_path(index), 0,
                                 "项目索引的知识文件链接 %d 个与 20-知识 实物 %d 篇不符"
                                 % (n, len(files))))
    return out


def check_index_consistency() -> list[L.Finding]:
    """A14 全量:根索引清单 + 项目索引链接数(判据见模块 docstring)。"""
    return check_root_lists_projects() + check_project_index_links()


def index_hints(verbose: bool = True) -> list[str]:
    """提示通道:根索引尚未创建时给一行(不计入 FAIL,判据见模块 docstring)。"""
    if (L.VAULT_ROOT / L.PROJECT_INDEX).is_file():
        return []
    dirs = project_subdirs()
    if not dirs:
        return []
    out = ["[提示] 根 %s 未创建,%d 个项目目录未登记(不计入 FAIL;A14 清单检查已跳过)"
           % (L.PROJECT_INDEX, len(dirs))]
    if verbose:
        out.append("   待登记:%s" % "、".join(d.name for d in dirs))
    return out
