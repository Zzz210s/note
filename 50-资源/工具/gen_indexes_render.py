#!/usr/bin/env python3
"""Task 8 生成器的渲染层:项目索引页(五块)与根索引(一页)。

口径(对齐巡检):
- 项目索引页统计行须落在前 8 行(`checks_project._head`),故 frontmatter 只留 `type`/`status`;
- `## 知识产出` 每篇知识恰好一条文件链接(A14② 数链接),`## 计划与进度` / `## 原料` /
  `## 知识产出` / `## 模板` / `## 出口` 为固定五块;
- 根索引用**完整路径链接**列全部子目录(A14① 子串判定),路线条目链接各项目
  `!项目说明.md`(A7 反向判定),汇总行 `> 全库知识 N 篇 · 项目 M 个`(A9)。
"""
from __future__ import annotations

from gen_indexes_lib import (CONTAINERS, INSTRUCTION, KNOWLEDGE, PROJECTS, ROOT, ROOT_PREFIX,
                             TRACKER, dedup, rebase, status_of)

TEMPLATES = {
    "2026-掌握西班牙语B2": ("西班牙语-周计划模板.md", "西班牙语-每日笔记模板.md"),
    "!六级英语每日一练": ("六级-每日笔记模板.md",),
    "!一天一道算法题": ("算法-每日笔记模板.md",),
}


def render_project(name: str, data: dict) -> str:
    proj = ROOT / PROJECTS / name
    status = status_of(proj)
    has_spec = (proj / INSTRUCTION).is_file()
    kd = proj / KNOWLEDGE
    files = sorted(kd.glob("*.md")) if kd.is_dir() else []
    n = len(files)
    out = ["---", "type: note", "status: %s" % status, "---", "",
           "# %s" % name, "",
           "> 本项目知识 %d 篇 · 状态 %s · 覆盖 %d/%d(100%%)" % (n, status, n, n), ""]
    if has_spec:
        out += ["**入口:** [!项目说明.md](<!项目说明.md>)(目标 / 验收 / 任务清单)。", ""]
    else:
        out += ["**这是什么:** 常驻的问题追踪目录(无时间盒、不归档);修完即删条目。", ""]
    out += ["## 计划与进度", ""]
    out += [rebase(e, name) for e in data.get("计划与进度", [])] or \
        (["- [ ] 完成 [!项目说明.md](<!项目说明.md>) 的任务清单与验收。"] if has_spec
         else ["- [ ] 逐条修完下面的问题清单(修完即删条目)。"])
    out += ["", "## 原料", ""]
    out += [rebase(e, name) for e in data.get("原料", [])] or \
        ["- 仅本机原料放 `50-资源/%s/`(不进版本控制);有值得入库的长文再在此登记。" % name]
    out += ["", "## 知识产出", ""]
    entries = dedup(data.get("知识产出", []))
    lines = [rebase(e, name) for e in entries]
    covered = {e["target"].rsplit("/", 1)[-1][:-3] for e in entries}
    lines += ["- [%s](<%s/%s>)" % (f.stem, KNOWLEDGE, f.name)
              for f in files if f.stem not in covered]
    out += lines or ["- (暂无成品知识;学成后写进 `20-知识/` 并在此登记一行。)"]
    out += ["", "## 模板", ""]
    for t in TEMPLATES.get(name, ()):
        out.append("- [`90-模板/%s`](../../90-模板/%s)" % (t, t))
    if name not in TEMPLATES:
        out.append("- 暂无专属模板;需要时放项目内 `90-模板/` 或全局 `90-模板/`。")
    out += ["", "## 出口", ""]
    if has_spec:
        out.append("- 完成后整包移入 `40-归档/%s/`,并在根 [`00-索引.md`](../../00-索引/00-索引.md) 更新登记。" % name)
    else:
        out.append("- 不归档;问题清单修完即在本页删条目。")
    return "\n".join(out) + "\n"


def render_root(dests: dict) -> str:
    dirs = sorted(p for p in (ROOT / PROJECTS).iterdir() if p.is_dir())
    n_know = sum(len(sorted((d / KNOWLEDGE).glob("*.md"))) for d in dirs
                 if (d / KNOWLEDGE).is_dir())
    n_proj = sum(1 for d in dirs if (d / INSTRUCTION).is_file())
    out = ["# 0-Note 索引", "",
           "> 全库知识 %d 篇 · 项目 %d 个" % (n_know, n_proj), "",
           "**这是什么:** 全库唯一入口。项目自足(计划 / 原料 / 知识 / 模板 / 出口 都在项目自己的",
           "`00-索引.md` 里),这一页只做项目总览与全局学习路线;原料(`50-资源/`)仅本机、不进版本控制。",
           "", "## 计划与进度", ""]
    out += [rebase(e, "__ROOT__") for e in dests.get("__ROOT__", {}).get("计划与进度", [])]
    out += ["", "## 项目清单", "",
            "| 目录 | 类型 | 状态 | 知识 | 入口 |", "| --- | --- | --- | --- | --- |"]
    for d in dirs:
        name = d.name
        kind = "容器" if name in CONTAINERS else ("追踪" if name == TRACKER else "项目")
        status = "常驻" if name in CONTAINERS else status_of(d)
        kd = d / KNOWLEDGE
        n = len(sorted(kd.glob("*.md"))) if kd.is_dir() else 0
        entry = "[索引](<%s%s/%s/00-索引.md>)" % (ROOT_PREFIX, PROJECTS, name)
        if (d / INSTRUCTION).is_file():
            entry += " · [说明](<%s%s/%s/%s>)" % (ROOT_PREFIX, PROJECTS, name, INSTRUCTION)
        out.append("| %s | %s | %s | %d | %s |" % (name, kind, status, n, entry))
    return "\n".join(out) + "\n"
