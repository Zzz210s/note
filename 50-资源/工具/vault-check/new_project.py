#!/usr/bin/env python3
"""建新项目脚手架(0-Note 项目引导结构)。

用法(Windows 必须带 PYTHONIOENCODING=utf-8):
    python -B 50-资源/工具/vault-check/new_project.py <项目名> --type 学习|常驻|通用 \
        [--goal "一句话目标"] [--template 用途] [--dry-run]
    python -B 50-资源/工具/vault-check/new_project.py --backfill [--dry-run]

生成物(所有类型):
    10-项目/<名>/00-索引.md      五块索引页(复用 gen_indexes_render,统计行在前 8 行)
    10-项目/<名>/20-知识/.gitkeep
    50-资源/<名>/                 仅本机原料(50-资源/* 已被 .gitignore 忽略,不入库)
    根 00-索引.md                 追加清单行 + 汇总行 N/M 同步
类型:
    学习  有目标有截止 → 另建 `!项目说明.md` + teach 协议(MISSION / RESOURCES / NOTES),
          并在根索引「计划与进度」补一条路线行
    常驻  常驻容器(约定 `!` 前缀,如 `!名词解释`):无时间盒、不归档,只建容器骨架
    通用  通用收集区(不带 `!` 前缀的常驻项目),件同常驻

幂等:已存在的文件一律不覆盖;重复跑只补缺失件。`--dry-run` 只打印将创建的内容与索引改动。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L                      # noqa: E402  frontmatter 解析(与巡检同源)
import new_project_lib as S                # noqa: E402
import new_project_register as G           # noqa: E402

VAULT = S.VAULT
KINDS = ("学习", "常驻", "通用")
ROOT_INDEX = G.ROOT_INDEX


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(VAULT)).replace("\\", "/")
    except ValueError:
        return str(path)


def status_of(name: str) -> str:
    f = VAULT / S.PROJECTS / name / S.INSTRUCTION
    fm = L.parse_frontmatter(L.read_text(f)) if f.is_file() else None
    return (fm or {}).get("status", "todo").strip('"').strip("'") or "todo"


def knowledge_count(name: str) -> int:
    kd = VAULT / S.PROJECTS / name / S.KNOWLEDGE
    return len(list(kd.rglob("*.md"))) if kd.is_dir() else 0


def row_for(name: str, kind: str, status: str, spec: bool) -> str:
    entry = "[索引](<%s/%s/%s>)" % (S.PROJECTS, name, S.INDEX)
    if spec:
        entry += " · [说明](<%s/%s/%s>)" % (S.PROJECTS, name, S.INSTRUCTION)
    return "| %s | %s | %s | %d | %s |" % (name, kind, status, knowledge_count(name), entry)


def plan_new(name: str, kind: str, goal: str | None, tpl: str | None) -> list[tuple[Path, str | None]]:
    """(路径, 内容) 清单,内容 None 表示只建目录。"""
    proj = VAULT / S.PROJECTS / name
    acts: list[tuple[Path, str | None]] = [(proj, None)]
    if kind == "学习":
        acts.append((proj / S.INSTRUCTION, S.instruction_text(name, goal)))
        acts += [(proj / f, text) for f, text in S.teach_files(name).items()]
    acts.append((proj / S.KNOWLEDGE / ".gitkeep", ""))
    acts.append((VAULT / S.RESOURCE_DIR / name, None))
    if tpl:
        acts.append((S.TEMPLATE_DIR / ("%s-%s模板.md" % (name, tpl)), S.template_text(name, tpl)))
    index = S.render_index_planned(name, kind == "学习")
    if tpl:
        index = S.link_template(index, name, tpl)
    acts.append((proj / S.INDEX, index))
    return acts


def emit(path: Path, content: str | None, dry: bool) -> str:
    """落盘一件(或只报告);返回一行状态。"""
    if content is None or path.is_dir():
        if path.is_dir():
            return "已存在目录 %s/" % rel(path)
        if not dry:
            path.mkdir(parents=True, exist_ok=True)
        return "%s目录 %s/" % ("将建" if dry else "新建", rel(path))
    if path.exists():
        return "已存在文件 %s" % rel(path)
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return "%s文件 %s" % ("将建" if dry else "新建", rel(path))


def write_root(text: str, dry: bool) -> str:
    if not dry:
        ROOT_INDEX.write_text(text, encoding="utf-8", newline="\n")
    return "%s %s" % ("将改" if dry else "更新", rel(ROOT_INDEX))


def register(name: str, kind: str, goal: str | None, dry: bool) -> None:
    """根索引登记:清单行 + (学习型)路线行 + 汇总行同步。"""
    old = ROOT_INDEX.read_text(encoding="utf-8")
    spec = kind == "学习"
    cell = {"学习": "项目", "常驻": "容器", "通用": "通用"}[kind]
    new = G.add_project_row(old, name, row_for(name, cell, "todo" if spec else "常驻", spec))
    if spec:
        line = "- [ ] [%s](<%s/%s/%s>)" % (name, S.PROJECTS, name, S.INSTRUCTION)
        if goal:
            line += " — %s" % goal
        new = G.add_plan_line(new, name, line)
    know, proj = G.vault_counts()
    if spec and not (VAULT / S.PROJECTS / name / S.INSTRUCTION).is_file():
        proj += 1                      # 没落盘(dry-run)时按「即将多一个项目」算
    new = G.sync_summary(new, know, proj)
    if new == old:
        print("已存在 根索引已登记 %s" % name)
        return
    print("%s %s" % (write_root(new, dry), "(新增 %d 行)" % len(G.added_lines(old, new))))
    if dry:
        for line in G.added_lines(old, new):
            print("    + %s" % line)


def show(acts: list[tuple[Path, str | None]], dry: bool) -> None:
    for path, content in acts:
        print("  %s" % emit(path, content, dry))
        if dry and content:
            print("    --- %s ---" % rel(path))
            for line in content.splitlines():
                print("    | %s" % line)


# ---------------------------------------------------------------- 回溯补齐

def backfill(dry: bool) -> None:
    """既有目录补齐:缺 `20-知识/` 的建 .gitkeep;非容器建 `50-资源/<名>/`;根索引核对。"""
    print("[回溯] 10-项目/ 下既有目录:")
    for d in sorted((VAULT / S.PROJECTS).iterdir()):
        if not d.is_dir():
            continue
        kd = d / S.KNOWLEDGE
        if not kd.is_dir() or not any(kd.iterdir()):
            print("  %s" % emit(kd / ".gitkeep", "", dry))
        if d.name not in S.CONTAINERS:
            print("  %s" % emit(VAULT / S.RESOURCE_DIR / d.name, None, dry))
        if not (d / S.INDEX).is_file():
            print("  %s" % emit(d / S.INDEX, S.render_index(d.name), dry))
    old = ROOT_INDEX.read_text(encoding="utf-8")
    new = old
    for d in sorted((VAULT / S.PROJECTS).iterdir()):
        if not d.is_dir() or d.name in G.listed_names(new):
            continue
        kind = "容器" if d.name in S.CONTAINERS else "项目"
        spec = (d / S.INSTRUCTION).is_file()
        if kind == "容器":
            new = G.add_project_row(new, d.name, row_for(d.name, kind, "常驻", False))
        else:
            new = G.add_project_row(new, d.name, row_for(d.name, kind, status_of(d.name), spec))
    know, proj = G.vault_counts()
    new = G.sync_summary(new, know, proj)
    if new == old:
        print("[回溯] 根索引已列全 %d 个目录,汇总行无需改" % len(G.listed_names(new)))
    else:
        print("[回溯] %s" % write_root(new, dry))
        for line in G.added_lines(old, new):
            print("    + %s" % line)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="建新项目脚手架(0-Note 项目引导结构)")
    ap.add_argument("name", nargs="?", help="项目名(不含路径)")
    ap.add_argument("--type", dest="kind", choices=KINDS, help="项目类型")
    ap.add_argument("--goal", help="一句话目标(写进 !项目说明.md 与根索引路线行)")
    ap.add_argument("--template", dest="tpl", help="专属模板用途 → 90-模板/<项目名>-<用途>模板.md")
    ap.add_argument("--backfill", action="store_true", help="回溯补齐既有项目缺失件")
    ap.add_argument("--dry-run", action="store_true", help="只打印将创建 / 修改的内容")
    args = ap.parse_args(argv)

    if args.backfill:
        backfill(args.dry_run)
        return 0
    if not args.name or not args.kind:
        ap.error("要么给 <项目名> --type <学习|常驻|通用>,要么用 --backfill")
    name = args.name.strip()
    if not name or name in (".", "..") or set(name) & set("/\\"):
        ap.error("项目名不能为空、不能含路径分隔符:%r" % args.name)
    if args.kind == "常驻" and not name.startswith("!"):
        print("提示:常驻容器约定 `!` 前缀(如 `!名词解释`);当前名 %s 未带前缀。" % name)
    print("[新建] %s(--type %s%s)" % (name, args.kind, ",dry-run" if args.dry_run else ""))
    show(plan_new(name, args.kind, args.goal, args.tpl), args.dry_run)
    register(name, args.kind, args.goal, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
