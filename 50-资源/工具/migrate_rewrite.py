#!/usr/bin/env python3
"""迁移脚本的引用改写:markdown 链接与路径式双链按旧位置解析、按新位置重写。

把 `20-领域/` 的成品知识搬进 `10-项目/<项目或容器>/20-知识/`,引用要跟着改。三条口径:

- 搬家文件的链接**按旧位置解析、按新位置算相对路径** —— 不这么分,搬过的笔记里那些
  「同目录互引」会全部漏改(apply 后它已在新家,解析基准必须仍是旧位置)。
- 输出写法:目标路径含空格或非 ASCII 时**强制 `<...>` 包裹**(Markdown 里裸写 `](a b.md)`
  会断,西语目录名带空格就是这一种);原本就带 `<>` 的保持,`#锚点` 与结尾斜杠保留。
- 围栏代码块里的示例不动(与巡检 A1 的 strip_code 同口径),行尾原样保留(二进制读写)。

编排(移动、空目录清理、MOC 统计块刷新)在 `migrate_engine.py` 与本文件的调用方
`migrate-notes.py`;拆文件的唯一理由是每个自研文件守住 ≤200 行。
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from migrate_engine import SKIP_DIRS, VAULT, read, rel, write

LINK_RE = re.compile(r"\]\((?:<([^>]+)>|([^)\s]+))\)")
WIKI_RE = re.compile(r"\[\[([^\]]+)\]\]")
FENCE = re.compile(r"^\s*(```|~~~)")


def md_link(target: str, bracketed: bool) -> str:
    """markdown 链接写法:含空格或非 ASCII 的目标必须 `<...>` 包裹,否则链接断掉。"""
    if bracketed or any(c.isspace() or ord(c) > 127 for c in target):
        return "](<%s>)" % target
    return "](%s)" % target


def retarget(raw: str, base: Path, out_dir: Path, files: dict[Path, Path],
             dirs: dict[Path, Path]) -> str | None:
    """markdown 链接目标:命中被搬走的文件/目录则返回新写法(相对 out_dir),否则 None。

    base = 解析基准(搬家文件用旧位置),out_dir = 输出基准(文件最终所在目录)。
    """
    if raw.startswith(("http", "#", "mailto")):
        return None
    body, sep, anchor = raw.partition("#")
    slashed = body.endswith("/")
    body = body.rstrip("/")
    if not body:
        return None
    new = files.get((base / body).resolve()) or dirs.get((base / body).resolve())
    if new is None:
        return None
    tail = os.path.relpath(new, out_dir).replace(os.sep, "/")
    return tail + ("/" if slashed else "") + (sep + anchor if sep else "")


def retarget_wiki(raw: str, moves: dict[str, str]) -> str | None:
    """路径式双链 `[[目录/名]]` 才改写(裸名唯一,搬完照样解析得到)。"""
    target, pipe, alias = raw.partition("|")
    core, hsep, frag = target.partition("#")
    core = core.strip().lstrip("/")
    if "/" not in core:
        return None
    for old, new in moves.items():
        stem_old, stem_new = old[:-3], new[:-3]
        if stem_old == core or stem_old.endswith("/" + core):
            return stem_new + hsep + frag + (pipe + alias if pipe else "")
    return None


def rewrite_file(p: Path, files: dict[Path, Path], dirs: dict[Path, Path],
                 moves: dict[str, str], base_map: dict[Path, Path], apply: bool) -> int:
    """改写一篇文章里的引用,返回改写处数。"""
    text = read(p)
    base, out_dir = base_map.get(p.resolve(), p.parent), p.parent
    hits = [0]

    def counted(rep: str, old: str) -> str:
        """写法没变就不算改写也不写盘(同目录互引搬完路径不变,幂等靠这一步)。"""
        if rep == old:
            return old
        hits[0] += 1
        return rep

    def md(m: re.Match[str]) -> str:
        new = retarget(m.group(1) or m.group(2), base, out_dir, files, dirs)
        if new is None:
            return m.group(0)
        return counted(md_link(new, m.group(1) is not None), m.group(0))

    def wiki(m: re.Match[str]) -> str:
        new = retarget_wiki(m.group(1), moves)
        return m.group(0) if new is None else counted("[[%s]]" % new, m.group(0))

    out, fence = [], False
    for line in text.splitlines(keepends=True):
        if FENCE.match(line):
            fence = not fence
        elif not fence:
            line = LINK_RE.sub(md, WIKI_RE.sub(wiki, line))
        out.append(line)
    if apply and hits[0]:
        write(p, "".join(out))
    return hits[0]


def rewrite_all(files: dict[Path, Path], dirs: dict[Path, Path], moves: dict[str, str],
                apply: bool) -> int:
    """全库扫一遍改写引用(跳过 AI 产物与工具目录)。"""
    base_map = {new: old.parent for old, new in files.items()}   # 同一张表派生:新家 → 旧目录
    total = 0
    for p in sorted(VAULT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        n = rewrite_file(p, files, dirs, moves, base_map, apply)
        if n:
            total += n
            print("  %s ×%d" % (rel(p), n))
    return total
