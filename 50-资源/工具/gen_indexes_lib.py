#!/usr/bin/env python3
"""Task 8 生成器的公共层:读旧 MOC、按链接目标归属条目、重锚相对路径。

归属按旧 MOC 条目的**链接目标**判定(不按 MOC 名):知识 → 该项目 `20-知识/`,每日笔记 →
计划,`50-资源` → 原料;`- [ ]` 待办按 MOC 小节判定。两个容器的条目已在各自索引页里,只对账
不重生成;`00-索引/*.md` 的 MOC 互链随 MOC 一起退役。
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOC_DIR = ROOT / "00-索引"
MOC_NAMES = ("系统.md", "外语.md", "算法.md", "编程语言.md", "AI-agent.md")
CONTAINERS = ("!名词解释", "!系统与工具")
TRACKER = "!问题追踪"
INSTRUCTION = "!项目说明.md"
KNOWLEDGE = "20-知识"
PROJECTS = "10-项目"
# 条目行里的第一个 markdown 链接(`- [ ] [标题](<路径>)` / `- [已落地] 说明 -> [标题](<路径>)`)
LINK_RE = re.compile(r"\[(?P<title>[^\]]*)\]\(<(?P<target>[^>]+)>\)")


def vrel(target: str) -> str | None:
    """MOC 里的相对目标 → 仓库根相对 posix 路径(文件不存在也算,路径搬家靠它)。"""
    t = target.split("#")[0].strip()
    if not t or t.startswith(("http", "mailto")):
        return None
    try:
        return (MOC_DIR / t).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def parse_mocs() -> list[dict]:
    """每张旧 MOC 的条目行(带所属 h2/h3 小节与解析后的目标)。"""
    out: list[dict] = []
    for name in MOC_NAMES:
        sec2 = sec3 = ""
        for line in (MOC_DIR / name).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^(#{2,3})\s+(.*)$", line)
            if m:
                if len(m.group(1)) == 2:
                    sec2, sec3 = m.group(2), ""
                else:
                    sec3 = m.group(2)
            elif line.startswith("- ["):
                m2 = LINK_RE.search(line)
                out.append({"moc": name, "sec": sec2, "sub": sec3, "line": line,
                            "target": vrel(m2.group("target")) if m2 else None})
    return out


def classify(e: dict) -> tuple[str, str] | None:
    """条目 → (去向, 块);去向可为项目名 / 哨兵 / 容器名;None 表示未归类(要报)。"""
    if e["line"].startswith("- [ ]"):
        if e["moc"] == "算法.md":
            return "!一天一道算法题", "计划与进度"
        if e["moc"] == "系统.md" and e["sec"].startswith("学习路线"):
            return "__ROOT__", "计划与进度"
        return None
    v = e["target"]
    if not v:
        return None
    if v.startswith("00-索引/"):
        return "__OBSOLETE__", "MOC 互链"
    if v.startswith(PROJECTS + "/"):
        proj = v.split("/")[1]
        if "/%s/" % KNOWLEDGE in v:
            return proj, "知识产出"
        if "/08-每日笔记/" in v:
            return proj, "计划与进度"
        if proj == TRACKER:
            return proj, "知识产出"
        return None
    if v.startswith("50-资源/记录/"):
        return "!系统与工具", "原料"
    if v.startswith("50-资源/Zephyr/"):
        return "2026Q4-参与Zephyr开源社区", "原料"
    if v.startswith("50-资源/工具/"):
        return "2026-10-掌握Markdown", "原料"
    return None


def rebase(e: dict, dest: str) -> str:
    """把条目行里的链接目标改成目标索引页的相对路径(其余文本原样保留)。"""
    m = LINK_RE.search(e["line"])
    if not m or not e["target"]:
        return e["line"]
    base = ROOT if dest == "__ROOT__" else ROOT / PROJECTS / dest
    new = os.path.relpath(ROOT / e["target"], base).replace("\\", "/")
    return "%s[%s](<%s>)%s" % (e["line"][:m.start()], m.group("title"), new, e["line"][m.end():])


def dedup(entries: list[dict]) -> list[dict]:
    """同一目标只留第一条(A14② 每篇恰好一条链接)。"""
    seen: set[str] = set()
    out: list[dict] = []
    for e in entries:
        if e["target"] in seen:
            continue
        seen.add(e["target"])
        out.append(e)
    return out


def status_of(proj: Path) -> str:
    f = proj / INSTRUCTION
    if not f.is_file():
        return "todo"
    m = re.search(r"^status:\s*(\S+)", f.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "todo"


def subdirs() -> list[Path]:
    return sorted(p for p in (ROOT / PROJECTS).iterdir() if p.is_dir())


def build() -> tuple[dict, dict, list]:
    """(项目→块→条目, 计数, 未归类)。根路线条目同时拷进对应项目的「计划与进度」。"""
    dests: dict[str, dict[str, list[dict]]] = {}
    stats = {"__ROOT__": 0, "__OBSOLETE__": 0, "container": 0}
    unmapped: list[dict] = []
    for e in parse_mocs():
        c = classify(e)
        if c is None:
            unmapped.append(e)
            continue
        dest, block = c
        if dest in CONTAINERS:
            stats["container"] += 1
            continue
        if dest == "__ROOT__":
            stats["__ROOT__"] += 1
            dests.setdefault("__ROOT__", {}).setdefault(block, []).append(e)
            proj = e["target"].split("/")[1]
            dests.setdefault(proj, {}).setdefault(block, []).append(dict(e, copy=True))
            continue
        if dest == "__OBSOLETE__":
            stats["__OBSOLETE__"] += 1
            continue
        dests.setdefault(dest, {}).setdefault(block, []).append(e)
    return dests, stats, unmapped
