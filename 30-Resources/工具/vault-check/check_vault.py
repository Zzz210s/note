#!/usr/bin/env python3
"""0-Note 巡检:A1 断链 / A2 双链失效 / A3 孤篇 / A4 MOC 覆盖 / A5 type-status / A6 frontmatter / A7 路线一致性。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

ALLOWED_TYPES = {"algorithm", "project", "system", "language", "tutorial", "log", "note", "concept"}
ALLOWED_STATUS = {"todo", "learning", "done", "review"}
FM_EXEMPT = ("00-MOC/", "90-Templates/", "README", "10-Projects/!问题追踪/")
# 00-MOC/ 与 FM_EXEMPT 同口径:它是索引入口层(由 README 指向),不要求自身有入链
ORPHAN_EXEMPT = ("00-MOC/", "40-Archive/", "90-Templates/")
MAX_FIELDS = 8

# A4 的扫描范围:知识区 + 原料区。40-Archive 归档区允许孤立,90-Templates 是模板层,均不扫。
SCAN_ROOTS = ("20-Areas", "30-Resources")


def _rel(p: Path) -> str:
    return L.rel_path(p)


def _scan_files() -> list[Path]:
    """A4 的待检文件:20-Areas + 30-Resources 下全部 .md。"""
    out: list[Path] = []
    for r in SCAN_ROOTS:
        out.extend(sorted((L.VAULT_ROOT / r).rglob("*.md")))
    return out


def check_links() -> list[L.Finding]:
    out: list[L.Finding] = []
    for p in L.iter_md_files(L.VAULT_ROOT):
        for line, target in L.extract_links(L.read_text(p)):
            if target.startswith(("http", "#", "mailto")):
                continue
            bare = target.split("#")[0]
            if not bare or any(target.startswith(w) for w in L.LINK_WHITELIST):
                continue
            if not (p.parent / bare).resolve().exists():
                out.append(L.Finding("A1", _rel(p), line, target))
    return out


def check_wikilinks() -> list[L.Finding]:
    """Obsidian 语义:[[note]] 按文件名命中;[[folder/note]] 按路径后缀命中。

    注意(任务 1 审查发现):本库有 18 个同名 `!项目说明.md`,只比对裸文件名会把
    路径形式的失效链接误判为有效,所以路径形式必须按后缀解析。
    """
    stems = L.md_stems(L.VAULT_ROOT)
    rels = [str(q.relative_to(L.VAULT_ROOT).with_suffix("")).replace("\\", "/")
            for q in L.iter_md_files(L.VAULT_ROOT)]
    out: list[L.Finding] = []
    for p in L.iter_md_files(L.VAULT_ROOT):
        for line, target in L.extract_wikilinks(L.read_text(p)):
            core = target.split("|")[0].strip()
            if core in L.WIKILINK_WHITELIST:
                continue
            if "/" in core:
                if any(r == core or r.endswith("/" + core) for r in rels):
                    continue
            elif core in stems:
                continue
            out.append(L.Finding("A2", _rel(p), line, target))
    return out


def check_orphans() -> list[L.Finding]:
    """A3:全库无入链的笔记。扫描范围本就是全库(含 30-Resources),只按 ORPHAN_EXEMPT 豁免;
    入链来源同样取自全库,所以不会漏掉「被 10-Projects 引用」的 30-Resources 笔记。
    """
    files = list(L.iter_md_files(L.VAULT_ROOT))
    linked: set[Path] = set()
    stems = L.md_stems(L.VAULT_ROOT)
    for p in files:
        text = L.read_text(p)
        for _, target in L.extract_links(text):
            bare = target.split("#")[0]
            if bare and not target.startswith(("http", "#")):
                linked.add((p.parent / bare).resolve())
        for _, target in L.extract_wikilinks(text):
            core = target.split("|")[0].strip().split("/")[-1]
            if core in stems:
                linked.add(Path(core))
    out: list[L.Finding] = []
    for p in files:
        rel = _rel(p)
        if any(rel.startswith(e) for e in ORPHAN_EXEMPT):
            continue
        if p.resolve() in linked or Path(p.stem) in linked:
            continue
        out.append(L.Finding("A3", rel, 0, "无入链"))
    return out


def check_meta() -> list[L.Finding]:
    out: list[L.Finding] = []
    for p in L.iter_md_files(L.VAULT_ROOT):
        rel = _rel(p)
        if any(rel.startswith(e) for e in FM_EXEMPT):
            continue
        fm = L.parse_frontmatter(L.read_text(p))
        if fm is None:
            out.append(L.Finding("A6", rel, 0, "缺 frontmatter"))
            continue
        if len(fm) > MAX_FIELDS:
            out.append(L.Finding("A5", rel, 0, "字段数 %d > %d" % (len(fm), MAX_FIELDS)))
        t = fm.get("type", "").strip().strip('"').strip("'")
        if t not in ALLOWED_TYPES:
            out.append(L.Finding("A5", rel, 0, "type=%s 非规范值" % t))
        s = fm.get("status", "").strip().strip('"').strip("'")
        if s not in ALLOWED_STATUS:
            out.append(L.Finding("A5", rel, 0, "status=%s 非规范值" % s))
    return out


def check_moc_coverage() -> list[L.Finding]:
    """A4:20-Areas + 30-Resources 下每篇是否在任一 MOC 文本中出现。

    30-Resources 原来不在扫描范围,笔记一从 20-Areas 移过去就永久脱离 A3/A4 视野。
    """
    mocs = sorted((L.VAULT_ROOT / "00-MOC").glob("*.md"))
    blob = "".join(L.read_text(m) for m in mocs)
    out: list[L.Finding] = []
    for p in _scan_files():
        if p.name not in blob:
            out.append(L.Finding("A4", _rel(p), 0, "未在任一 MOC 出现"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="0-Note 巡检")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--moc-stats", action="store_true")
    args = ap.parse_args(argv)

    if args.moc_stats:
        for line in L.moc_stats():
            print(line)
        return 0

    groups = [("A1 断链", check_links()), ("A2 双链失效", check_wikilinks()),
              ("A3 孤篇", check_orphans()), ("A4 MOC 未覆盖", check_moc_coverage()),
              ("A5/A6 元数据", check_meta()), ("A7 路线一致性", L.check_roadmap())]
    if args.json:
        print(json.dumps([{"stage": f.stage, "path": f.path, "line": f.line, "detail": f.detail}
                          for _, fs in groups for f in fs], ensure_ascii=False, indent=1))
    else:
        for name, fs in groups:
            print("[%s] %d 处" % (name, len(fs)))
            if not args.quiet:
                for f in fs:
                    print("   %s:%s %s" % (f.path, f.line, f.detail))
    bad = sum(len(fs) for _, fs in groups)
    print("结论:%s" % ("PASS" if bad == 0 else "FAIL"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
