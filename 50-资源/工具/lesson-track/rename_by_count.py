#!/usr/bin/env python3
"""按阅读次数给课件改名:`0001-x.html` → `x3-0001-x.html`(读过的排到没读过的后面)。

用户定的规则(2026-09-27):
- 名字最前面是 `x<次数>-`,其中 `x` 是**无意义前缀**,只为了排序 —— 字母排在数字之后,
  所以**读过的课永远排在没读过的课下面**;读过的课之间按次数从小到大(`x1-` < `x2-` < `x10-`)。
- 次数为 0(没读过)**不加前缀**,保持原样排在上面。
- 次数取 `counts.json` 的 `count`(服务计数与 VS Code 历史取最大值,见 `track_lib.py`)。

改名会牵动引用,所以本脚本一气做完四件事:
1. 合并计数(`track_lib.merge_history()`);
2. 算出每个课件的目标名;
3. **重写全库文本里的文件名**(课间相对链接、锚点链接、各项目 `00-索引.md` 的课程块……);
4. 改名(`git mv` 保留历史,失败则退回普通改名),并可选地只提交这些改动。

用法:
    python -B rename_by_count.py            # 预览(不改任何文件)
    python -B rename_by_count.py --apply    # 真的改 + 更新索引
    python -B rename_by_count.py --apply --commit   # 再 git 提交这些改动(显式路径,不用 -A)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import track_lib as T

PREFIX_RE = re.compile(r"^x\d+-")
SKIP_PARTS = {".git", "node_modules", ".superpowers", "docs", "50-资源"}
TEXT_SUFFIXES = (".html", ".md")


def base_name(name: str) -> str:
    """去掉 `x<次数>-` 前缀,得到稳定标识。"""
    return PREFIX_RE.sub("", name)


def target_name(base: str, count: int) -> str:
    return ("x%d-%s" % (count, base)) if count > 0 else base


def course_files() -> list[Path]:
    base = T.VAULT / "10-项目"
    out: list[Path] = []
    for proj in sorted(p for p in base.iterdir() if p.is_dir()):
        for kind in ("lessons", "reference"):
            out.extend(sorted((proj / kind).glob("*.html")))
    return out


def build_plan() -> dict[Path, Path]:
    """{现有路径: 目标路径}(只包含需要改名的)。"""
    counts = T.load()
    # 计数键按「项目/类别/去前缀文件名」归一,改名后依然认得出来
    by_base: dict[tuple[str, str, str], int] = {}
    for rel, rec in counts.items():
        parts = rel.split("/")
        if len(parts) < 4:
            continue
        key = (parts[1], parts[2], base_name(parts[-1]))
        by_base[key] = max(by_base.get(key, 0), int(rec.get("count", 0)))
    # 再建一张按「项目/类别/课号」的表:课件改过名时(历史里还是旧名字)靠它兜底
    by_num: dict[tuple[str, str, str], int] = {}
    for (proj, kind, base), n in by_base.items():
        num = base.split("-", 1)[0]
        k2 = (proj, kind, num)
        by_num[k2] = max(by_num.get(k2, 0), n)
    plan: dict[Path, Path] = {}
    for f in course_files():
        b = base_name(f.name)
        key = (f.parent.parent.name, f.parent.name, b)
        k2 = (f.parent.parent.name, f.parent.name, b.split("-", 1)[0])
        count = by_base.get(key, by_num.get(k2, 0))
        want = target_name(base_name(f.name), count)
        if want != f.name:
            plan[f] = f.with_name(want)
    return plan


def text_files() -> list[Path]:
    out = []
    for p in T.VAULT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel_parts = set(p.relative_to(T.VAULT).parts)
        if rel_parts & SKIP_PARTS:
            continue
        out.append(p)
    return out


def rewrite_refs(plan: dict[Path, Path]) -> list[Path]:
    """把全库文本里对这些文件的引用换成新名字;返回被改动的文件列表。"""
    pairs = [(f.name, new.name) for f, new in plan.items()]
    changed: list[Path] = []
    for p in text_files():
        try:
            s = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = s
        for old, dst in pairs:
            if old in new:
                # 整词替换:文件名前面可能是 / ( " 等,后面可能是 " > ) # 等 ——
                # 关键是不能把 `x1-0003-a.html` 里的 `0003-a.html` 再换一次(否则会叠成 x1-x1-…)
                pat = re.compile(r"(?<![\w-])" + re.escape(old) + r"(?![\w-])")
                new = pat.sub(lambda m: dst, new)
        if new != s:
            p.write_text(new, encoding="utf-8", newline="\n")
            changed.append(p)
    return changed


def rename_files(plan: dict[Path, Path]) -> int:
    done = 0
    for old, new in sorted(plan.items()):
        rel_old = old.relative_to(T.VAULT).as_posix()
        rel_new = new.relative_to(T.VAULT).as_posix()
        r = subprocess.run(["git", "-C", str(T.VAULT), "mv", "-f", str(old), str(new)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            new.parent.mkdir(parents=True, exist_ok=True)
            old.rename(new)
        done += 1
    return done


def commit(paths: list[Path], msg: str) -> None:
    rels = [p.relative_to(T.VAULT).as_posix() for p in paths]
    subprocess.run(["git", "-C", str(T.VAULT), "add", "--"] + rels, check=False)
    subprocess.run(["git", "-C", str(T.VAULT), "commit", "-q", "-m", msg], check=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="按阅读次数给课件改名")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args(argv)

    m = T.merge_history()
    plan = build_plan()
    print("计数:%d 个课件有记录(本次并入 %d 条);需要改名 %d 个" % (m["seen"], m["changed"], len(plan)))
    for old, new in sorted(plan.items(), key=lambda x: x[0].name):
        print("   %s  →  %s" % (old.name, new.name))
    if not args.apply:
        print("\n(预览模式:没有改动任何文件。加 --apply 才真的改。)")
        return 0
    res = apply_plan(plan, do_commit=args.commit)
    print("已重写 %d 个文件里的引用,改名 %d 个课件(索引里的链接随引用一起改)%s"
          % (len(res["refs"]), res["renamed"], ",并已提交" if res["committed"] else ""))
    return 0


def apply_plan(plan: dict[Path, Path], do_commit: bool = False) -> dict:
    """按计划改名 + 改引用(可选提交)。返回 {refs, renamed, committed}。"""
    refs = rewrite_refs(plan)
    renamed = rename_files(plan)
    committed = False
    if do_commit and plan:
        paths = list(plan.keys()) + list(plan.values()) + refs + [T.VAULT / "10-项目"]
        commit([p for p in paths if p.exists()] + list(plan.keys()),
               "chore(课程): 按阅读次数重命名课件")
        committed = True
    return {"refs": refs, "renamed": renamed, "committed": committed}


if __name__ == "__main__":
    raise SystemExit(main())
