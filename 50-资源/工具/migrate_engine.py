#!/usr/bin/env python3
"""migrate-notes.py 的引擎:公共路径助手 + 目录级映射 + A13 来源声明(与迁移计划表分开,
各守单一职责)。

引用改写(链接/双链重定向)在 `migrate_rewrite.py` —— 它反向 import 本文件的 VAULT /
SKIP_DIRS / rel / read / write,本文件不依赖它,不构成循环。

旧 MOC 统计块刷新(`refresh_mocs`)已随 `00-索引/` 目录删除而移除(2026-09-25 收尾轮):
它复算的 `checks_extra.MOC_DIRS` / `coverage()` 已整块清掉,库里也不再有 MOC。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]          # <库根>/50-资源/工具/migrate_engine.py
VAULT_CHECK = VAULT / "50-资源/工具/vault-check"
SKIP_DIRS = {".git", "node_modules", ".obsidian", ".trash", ".superpowers", "docs", "__pycache__"}


# A13 来源声明:项目知识笔记的 frontmatter 指回所属项目 `!项目说明.md`(容器不要求,不生成)
DECL_FMT = 'related: "[[%s/!项目说明|项目]]"'
SPEC = "!项目说明"


def rel(p: Path) -> str:
    """库根相对路径(posix)。"""
    return str(p.relative_to(VAULT)).replace("\\", "/")


def read(p: Path) -> str:
    return p.read_bytes().decode("utf-8")            # 二进制读写:绝不碰行尾


def write(p: Path, text: str) -> None:
    p.write_bytes(text.encode("utf-8"))


def _declare_file(p: Path, proj: str, apply: bool) -> int:
    """把来源声明并进 frontmatter 的 `related`(A13):已有 `related` 则转数组保留原值。

    只重写 frontmatter 块内那几行,正文与其余行尾按原样拼回;已经出现过本项目 `!项目说明`
    链接的(部分笔记 Task 6 前后就已写好)原样返回,故幂等。返回 1=已改、0=已声明、-1=跳过。
    """
    text = read(p)
    if not text.startswith("---"):
        print("  !! 无 frontmatter,跳过 %s" % rel(p))
        return -1
    end = text.find("\n---", 3)
    if end == -1 or not text[end:].startswith("\n---"):
        print("  !! frontmatter 不闭合,跳过 %s" % rel(p))
        return -1
    fm = text[3:end]
    if "%s/%s" % (proj, SPEC) in fm:
        return 0
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = fm.splitlines()
    want = '"[[%s/%s|项目]]"' % (proj, SPEC)
    idx = next((i for i, l in enumerate(lines) if re.match(r"related\s*:", l)), None)
    if idx is None:
        lines.append(DECL_FMT % proj)
    else:
        value = lines[idx].rstrip().split(":", 1)[1].strip()
        value = value[:-1].rstrip() if value.startswith("[") else value
        lines[idx] = "related: [%s, %s]" % (value, want)
    if apply:
        write(p, "---" + eol.join(lines) + eol + "---" + text[end + 4:])
    print("  %s  →  %s" % (rel(p), lines[idx if idx is not None else -1]))
    return 1


def declare_sources(moves: dict[str, str], apply: bool) -> None:
    """给搬进项目的知识笔记补来源声明(A13);容器豁免 —— 它没有「本项目」可指。

    dry-run 时新家还不存在,按旧位置读(文件正被搬,内容一样),好让预演的数字可信。
    """
    sys.path.insert(0, str(VAULT_CHECK))
    import vault_lib as L
    changed = already = skipped = 0
    for old, new in sorted(moves.items()):
        proj = new.split("/")[1]
        if L.is_container("%s/%s" % (L.PROJECT_ROOT, proj)):
            continue
        p = VAULT / new
        if not p.exists():
            p = VAULT / old
        if not p.exists():
            print("  !! 源与新家都不在,跳过 %s" % new)
            continue
        got = _declare_file(p, proj, apply)
        changed += got == 1
        already += got == 0
        skipped += got < 0
    print("  新增 %d 篇 · 已声明 %d 篇 · 跳过 %d 篇" % (changed, already, skipped))


def dir_map(table: dict[str, str], moves: dict[str, str]) -> dict[Path, Path]:
    """目录级映射:某条只在该旧目录被本批全部搬空、且都搬去同一个新目录时才生效。

    留了尾巴(目录里还有没搬的笔记)就不动 —— 否则那些仍在原地的笔记会被指到别的项目去。
    """
    out: dict[Path, Path] = {}
    for old, new in table.items():
        d = VAULT / old
        if not d.is_dir():
            continue
        files = [rel(p) for p in d.rglob("*.md")]
        if files and all(f in moves and moves[f].startswith(new + "/") for f in files):
            out[d.resolve()] = (VAULT / new).resolve()
    return out
