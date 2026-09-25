#!/usr/bin/env python3
"""根 `00-索引.md` 的登记:项目清单行、路线行、汇总计数。

根索引不整页重生成(旧 MOC 已删,`gen_indexes_lib.build()` 依赖它们),而是**增量改**:
插一行清单(按目录名排序,与 Task 8 生成顺序一致)、可选插一条路线行、再把汇总行的
N / M 按盘上实测同步。幂等:目标已在清单里就原样返回,汇总行由实测反推,重复跑不漂移。
"""
from __future__ import annotations

import re
from pathlib import Path

VAULT = Path(__file__).resolve().parents[3]
ROOT_INDEX = VAULT / "00-索引.md"
PROJECTS = "10-项目"
KNOWLEDGE = "20-知识"
INSTRUCTION = "!项目说明.md"

SUMMARY = re.compile(r"^> 全库知识 \d+ 篇 · 项目 \d+ 个", re.M)
PLAN_HEAD = re.compile(r"^##[ \t]+计划与进度", re.M)
TABLE_HEAD = ("目录", "---")


def vault_counts(root: Path = VAULT) -> tuple[int, int]:
    """(全库知识篇数, 项目个数) —— 与 A9 同口径:知识 = 各 `20-知识/` 的 .md 之和,
    项目 = 含 `!项目说明.md` 的目录数(`!问题追踪` 这类收集区不算)。"""
    base = root / PROJECTS
    if not base.is_dir():
        return 0, 0
    know = proj = 0
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        kd = d / KNOWLEDGE
        if kd.is_dir():
            know += len(list(kd.rglob("*.md")))
        if (d / INSTRUCTION).is_file():
            proj += 1
    return know, proj


def _first_cell(line: str) -> str:
    return line.split("|")[1].strip() if line.startswith("| ") else ""


def _row_lines(lines: list[str]) -> list[int]:
    """清单表的数据行下标(表头「目录」与分隔行「---」除外)。"""
    return [i for i, l in enumerate(lines)
            if l.startswith("| ") and _first_cell(l) not in TABLE_HEAD]


def listed_names(text: str) -> list[str]:
    return [_first_cell(l) for l in text.splitlines()
            if l.startswith("| ") and _first_cell(l) not in TABLE_HEAD]


def add_project_row(text: str, name: str, row: str) -> str:
    """在 `## 项目清单` 表里按目录名排序插入一行;同名行已在则不动。"""
    if name in listed_names(text):
        return text
    lines = text.splitlines()
    rows = _row_lines(lines)
    if not rows:
        return "\n".join(lines + [row]) + "\n"
    at = next((i for i in rows if _first_cell(lines[i]) > name), rows[-1] + 1)
    return "\n".join(lines[:at] + [row] + lines[at:]) + "\n"


def add_plan_line(text: str, name: str, line: str) -> str:
    """在「计划与进度」小节末尾插一条路线行;该小节里已出现项目名则不动。"""
    m = PLAN_HEAD.search(text)
    if not m:
        return text
    lines = text.splitlines()
    start = text[:m.start()].count("\n")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    if any(name in l for l in lines[start:end]):
        return text
    at = end
    while at > start + 1 and not lines[at - 1].strip():
        at -= 1
    return "\n".join(lines[:at] + [line] + lines[at:]) + "\n"


def sync_summary(text: str, know: int, proj: int) -> str:
    """汇总行同步为实测值;缺行时在 H1 之后补一行。"""
    new = "> 全库知识 %d 篇 · 项目 %d 个" % (know, proj)
    if SUMMARY.search(text):
        return SUMMARY.sub(new, text, count=1)
    lines = text.splitlines()
    at = 1 if lines and lines[0].startswith("# ") else 0
    return "\n".join(lines[:at] + ["", new] + lines[at:]).lstrip("\n") + "\n"


def added_lines(old: str, new: str) -> list[str]:
    """新增行(给 dry-run 打印用;汇总行被改写时也算进来)。"""
    before = old.splitlines()
    return [l for l in new.splitlines()
            if l not in before or l.startswith("> 全库知识") and l not in before]
