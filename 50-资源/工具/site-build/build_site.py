#!/usr/bin/env python3
"""0-Note 在线阅读站 · 入口(组装 + 断言 + CLI)。

```bash
python -B build_site.py                 # 两页都生成(index.html / all.html)
python -B build_site.py --public        # 只生成对外页(CI 用)
python -B build_site.py --all           # 只生成全库页
python -B build_site.py --out-dir DIR   # 换输出目录(CI 里传 $GITHUB_WORKSPACE)
```

三条断言(任一不过就报明确原因、退出码 1、**不写半成品**):
  1. 条目数与实时 `git ls-files` 计数一致(对外 = 课 + `20-知识` 笔记;全库 = md + html)
  2. 零外部资源:`<script src=` / `<link rel="stylesheet"` / `@import` 计数均为 0
  3. 体量门槛:对外 ≤ 1.6 MB,全库 ≤ 2.6 MB(工作台比旧阅读页重:外壳 + 两棵树 +
     预置笔记正文;实测 2026-10-02 公开 1.16 MB / 全库 1.89 MB)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import site_render
import site_scan

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT_ROOT = Path(__file__).resolve().parents[3]
GATES = {"public": 1_600_000, "all": 2_600_000}
OUT_NAME = {"public": "index.html", "all": "all.html"}


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=VAULT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip()


def content_rev() -> tuple[str, str]:
    """最近一次「内容提交」的短 sha 与日期(排除生成物 index.html)。

    站点页脚与 meta 里写的是它 —— 这样本地与 CI 对同一份内容产出**逐字节相同**的页面,
    CI 才不会因为 sha/日期变化而每次空提交(参考站同样处理)。
    """
    r = subprocess.run(["git", "log", "-1", "--format=%h	%cs", "--", "*.md", "*.html", ":!index.html"],
                       cwd=VAULT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    parts = (r.stdout.strip() or "unknown	unknown").split("	")
    return (parts[0], parts[1] if len(parts) > 1 else "unknown")


def live_counts() -> dict[str, int]:
    # 必须用 `-z`:CI 上 core.quotepath 默认为 true,普通输出会把中文路径转义成八进制,
    # 于是「/20-知识/」「/lessons/」这些匹配全部失效(2026-10-02 CI 实测 lessons=0)。
    out = subprocess.run(["git", "ls-files", "-z"], cwd=VAULT_ROOT, capture_output=True,
                         text=True, encoding="utf-8", errors="replace").stdout
    files = [p for p in out.split(chr(0)) if p.strip()]
    return {
        "md": sum(1 for p in files if p.endswith(".md")),
        "html": sum(1 for p in files if p.endswith(".html")),
        "lessons": sum(1 for p in files if "/lessons/" in p and p.endswith(".html")),
        "know": sum(1 for p in files if "/20-知识/" in p and p.endswith(".md")),
        "records": sum(1 for p in files if p.startswith("50-资源/记录/") and p.endswith(".md")),
    }


def check(mode: str, entries: list[dict], page: str) -> list[str]:
    live = live_counts()
    errs: list[str] = []
    if mode == "public":
        courses = sum(1 for e in entries if e["kind"] == "lesson")
        know = sum(1 for e in entries if "/20-知识/" in e["path"])
        records = sum(1 for e in entries if e.get("is_record"))
        if courses != live["lessons"]:
            errs.append("对外页课程数 %d != 实时 lessons %d" % (courses, live["lessons"]))
        if know != live["know"]:
            errs.append("对外页知识数 %d != 实时 20-知识 %d" % (know, live["know"]))
        if records != live["records"]:
            errs.append("对外页记录数 %d != 实时 记录 %d" % (records, live["records"]))
    elif len(entries) != live["md"] + live["html"]:
        errs.append("全库页条目 %d != 实时 md+html %d" % (len(entries), live["md"] + live["html"]))
    for bad, label in ((page.count("<script src="), "<script src="),
                       (page.count('<link rel="stylesheet"'), "<link rel=stylesheet"),
                       (page.count("@import"), "@import")):
        if bad:
            errs.append("页面含外部资源 %s x%d" % (label, bad))
    size = len(page.encode("utf-8"))
    if size > GATES[mode]:
        errs.append("体量 %d 字节 > 门槛 %d" % (size, GATES[mode]))
    return errs


def build(mode: str, out_dir: Path) -> Path:
    entries = site_scan.scan(mode)
    rev, when = content_rev()
    page = site_render.render_page(entries, mode=mode, generated_at=when, rev=rev)
    errs = check(mode, entries, page)
    if errs:
        print("[%s] 断言失败,未写出文件:" % mode)
        for e in errs:
            print("  - " + e)
        raise SystemExit(1)
    target = out_dir / OUT_NAME[mode]
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(page, encoding="utf-8", newline="\n")
    os.replace(tmp, target)
    print("[%s] %s · %d 条 · %d 字节 · 卡片 %d" % (mode, target, len(entries), len(page.encode("utf-8")), page.count('class="card"')))
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 0-Note 在线阅读站(对外 index.html / 全库 all.html)")
    ap.add_argument("--public", action="store_true", help="只生成对外页")
    ap.add_argument("--all", action="store_true", help="只生成全库页")
    ap.add_argument("--out-dir", default=str(VAULT_ROOT), help="输出目录(默认仓库根)")
    a = ap.parse_args()
    both = not (a.public or a.all)
    modes = [m for m in ("public", "all") if both or getattr(a, m)]
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for m in modes:
        build(m, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
