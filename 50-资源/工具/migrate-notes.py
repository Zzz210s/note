#!/usr/bin/env python3
"""migrate-notes.py — 0-Note 项目引导重构的数据迁移(规格第 5.2 节逐篇表)。

把 `20-领域/` 的成品知识搬进 `10-项目/<项目或容器>/20-知识/` 并改写全库引用;
引用改写与旧 MOC 统计块刷新在 `migrate_engine.py`,逐篇计划表在 `migrate_plan.py`
(本文件只放「迁移计划 + 编排」)。

用法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note
  python -B 50-资源/工具/migrate-notes.py --dry-run --filter "容器"
  python -B 50-资源/工具/migrate-notes.py --apply   --filter "项目"
  python -B 50-资源/工具/migrate-notes.py --dry-run --filter "!名词解释,!系统与工具"

三条硬要求(上次同类迁移踩过的坑,见任务简报):
 ① 映射单向:只有 `OLD_TO_NEW = {旧: 新}` 一张表,应用时只按旧读、按新写,不维护反向表。
 ② 目录级引用:`DIR_MAP` 覆盖 `20-领域/10-名词解释/` 这种以目录结尾的链接;某条只在该目录
    被本批全部搬空、且都搬去同一个新目录时才生效(见 engine.dir_map)。
 ③ 双链:`[[裸名]]` 在库内唯一,搬家后仍解析到同一篇,故不改;只有路径式 `[[目录/名]]` 才改写,
    且不带 `.md`(Obsidian 不认 `[[x.md]]`)。

幂等:旧路径没了、新路径在 → 跳过移动;改写按「解析后的绝对路径」查旧表,新路径不在旧表里,
重复跑不会二次改写;统计块按实测重算,结果没变则一字不动。源既不在旧位置、也不在新位置 =
迁移表的路径写错 → **直接非零退出**(dry-run 也报),不「静默成功」。

搬家的表按「目标目录 → 源文件清单」成组书写(在 `migrate_plan.py`):规格第 5.2 节里
每一行都保持原文件名,故目标路径可由目录 + 源文件名推出来,少写一半字,也把「改名」这种
意外变体挡在表外;唯一的例外是西语两个同名 `不规则动词.md`,进 `RENAMES` 显式消歧。

`--apply` 顺带做 A13 的来源声明:搬进项目的知识笔记在 frontmatter 加一条指回本项目
`!项目说明.md` 的 `related`(容器豁免)。它与移动同为幂等,重复跑只打印「已有」。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_engine import VAULT, declare_sources, dir_map, refresh_mocs, rel
from migrate_rewrite import rewrite_all

from migrate_plan import DIR_MAP, GROUPED, GROUPED_CONTAINERS, GROUPED_PROJECTS, OLD_TO_NEW


def find_missing(moves: dict[str, str]) -> list[str]:
    """源既不在旧位置、也不在新位置 → 迁移表路径写错(拼错/大小写不符/多余空格)。

    「旧没了但新在」是 apply 后复跑的合法状态,不算缺失。
    """
    return [old for old in sorted(moves)
            if not (VAULT / old).exists() and not (VAULT / moves[old]).exists()]


def do_moves(moves: dict[str, str], apply: bool) -> None:
    """`git mv` 逐个搬(保历史);不用 `git add -A`(共享仓库,只动显式路径)。

    源缺失的情况 main 已提前拦下(非零退出),这里只剩「已迁移」这一种分支。
    """
    for old, new in sorted(moves.items()):
        src, dst = VAULT / old, VAULT / new
        if not src.exists():
            print("  跳过(已迁移) %s" % old)
            continue
        print("  %s  →  %s" % (old, new))
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "mv", old, new], cwd=VAULT, check=True)


def prune_empty(moves: dict[str, str], apply: bool) -> list[str]:
    """搬完后空掉的 `20-领域` 目录,自底向上删(dry-run 按 moves 预演)。

    末尾连 `20-领域` 本身一起删(`rglob("*")` 不含自己,故显式补在队列最后):本批搬完
    它就是空壳,不该留在库里。
    """
    out: list[str] = []
    base = VAULT / "20-领域"
    if not base.is_dir():
        return out
    dirs = sorted((p for p in base.rglob("*") if p.is_dir()),
                  key=lambda p: len(p.parts), reverse=True)
    for d in dirs + [base]:
        if any(f.is_file() and rel(f) not in moves for f in d.rglob("*")):
            continue
        try:
            if apply:
                d.rmdir()
            out.append(rel(d))
        except OSError:
            print("  跳过非空目录 %s" % rel(d))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="0-Note 数据迁移(规格第 5.2 节)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="只打印将要做的移动与改写")
    g.add_argument("--apply", action="store_true", help="真正执行(git mv + 引用改写)")
    ap.add_argument("--filter", default="",
                    help='按新家目录名过滤("!名词解释,!系统与工具"),或分组关键词 "容器"/"项目"')
    args = ap.parse_args(argv)
    names = {s.strip() for s in args.filter.split(",") if s.strip()}
    if names == {"容器"}:                       # 分组关键词:省得手抄 8 个项目目录名
        names = {d.split("/")[1] for d in GROUPED_CONTAINERS}
    elif names == {"项目"}:
        names = {d.split("/")[1] for d in GROUPED_PROJECTS}
    moves = {o: n for o, n in OLD_TO_NEW.items() if not names or n.split("/")[1] in names}
    if not moves:
        print("没有匹配 --filter 的迁移条目")
        return 1
    missing = find_missing(moves)
    if missing:
        print("错误:以下 %d 条源文件既不在旧位置也不在新位置(请检查迁移表的路径):" % len(missing),
              file=sys.stderr)
        for old in missing:
            print("  %s" % old, file=sys.stderr)
        print("已中止,未做任何移动或改写", file=sys.stderr)
        return 2
    files = {(VAULT / o).resolve(): (VAULT / n).resolve() for o, n in moves.items()}
    dirs = dir_map(DIR_MAP, moves)
    print("模式:%s  过滤:%s  条目:%d" % ("apply" if args.apply else "dry-run",
                                    args.filter or "(全部)", len(moves)))
    print("目录级映射生效 %d 条:%s" % (len(dirs), "、".join(sorted(rel(k) for k in dirs)) or "无"))
    print("移动:")
    do_moves(moves, args.apply)
    print("引用改写:")
    print("  合计 %d 处" % rewrite_all(files, dirs, moves, args.apply))
    print("来源声明(A13):")
    declare_sources(moves, args.apply)
    empty = prune_empty(moves, args.apply)
    print("空目录清理 %d 个:%s" % (len(empty), "、".join(empty) or "无"))
    print("MOC 统计块:")
    refresh_mocs(moves, args.apply)
    print("完成(%s)" % ("已写入" if args.apply else "仅预演,未改动任何文件"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
