#!/usr/bin/env python3
"""Task 8:把 5 张旧 MOC 的条目按项目下移,生成 19 个项目索引页与根 `00-索引.md`。

用法:
    PYTHONIOENCODING=utf-8 python -B 50-资源/工具/gen_indexes.py --dry-run
    PYTHONIOENCODING=utf-8 python -B 50-资源/工具/gen_indexes.py --apply

公共层在 `gen_indexes_lib.py`,渲染层在 `gen_indexes_render.py`(每个文件守 200 行)。
dry-run 会逐项目打印条目数并断言全部 113 条 `- [` 行都已归类。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_indexes_lib as L
import gen_indexes_render as R


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="生成项目索引页与根索引(Task 8)")
    ap.add_argument("--apply", action="store_true", help="写入文件(默认只 dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="只打印条目去向(默认行为)")
    args = ap.parse_args(argv)
    dests, stats, unmapped = L.build()
    targets = [d for d in L.subdirs() if d.name not in L.CONTAINERS]
    total = 0
    for d in targets:
        data = dests.get(d.name, {})
        raw = sum(len([e for e in v if not e.get("copy")]) for v in data.values())
        total += raw
        print("  %-34s 计划 %2d 原料 %2d 知识 %2d(链接 %2d) = %2d 条" % (
            d.name, len(data.get("计划与进度", [])), len(data.get("原料", [])),
            len([e for e in data.get("知识产出", []) if not e.get("copy")]),
            len(L.dedup(data.get("知识产出", []))), raw))
    print("项目条目 %d;容器(已在各自索引) %d;根路线 %d;MOC 互链退役 %d"
          % (total, stats["container"], stats["__ROOT__"], stats["__OBSOLETE__"]))
    print("合计 %d 条(旧 MOC `- [` 行应为 113)"
          % (total + stats["container"] + stats["__ROOT__"] + stats["__OBSOLETE__"]))
    if unmapped:
        print("未归类 %d 条:" % len(unmapped))
        for e in unmapped:
            print("   %s | %s" % (e["moc"], e["line"][:100]))
        return 1
    if not args.apply:
        return 0
    for d in targets:
        (d / "00-索引.md").write_text(R.render_project(d.name, dests.get(d.name, {})),
                                      encoding="utf-8", newline="\n")
    (L.ROOT / "00-索引.md").write_text(R.render_root(dests), encoding="utf-8", newline="\n")
    print("已写入 %d 个项目索引页 + 根 00-索引.md" % len(targets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
