#!/usr/bin/env python3
"""课程访问次数的计数与回写(纯本机,不用 AI、不联网)。

分工:
- `counts.json`(与本文件同目录,不入库)是唯一真源:键是**相对仓库根的路径**,
  值是 `{"count": N, "first": "YYYY-MM-DD", "last": "YYYY-MM-DD"}`。
- 小服务 `server.py` 每收到一次课件请求就 `bump()` 一次。
- 回写:`write_index_suffixes()` 把次数追加到各项目 `00-索引.md` 课程块那一行尾部。
  它只改行尾的标记(**先剥掉旧标记再写新的**),所以重复跑是幂等的,也不会动别的字。

判定"这是课件"的口径:`10-项目/<项目>/(lessons|reference)/*.html` —— 覆盖所有
teach 工作区(21 个项目),与巡检 A11 的登记口径一致。
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

VAULT = Path(__file__).resolve().parents[3]
COUNT_FILE = Path(__file__).resolve().parent / "counts.json"
PROJECT_DIR = "10-项目"
COURSE_RE = re.compile(r"^10-项目/[^/]+/(lessons|reference)/[^/]+\.html$")
SUFFIX_RE = re.compile(r"\s*·\s*进入\s*\d+\s*次(?:\s*\(最近\s*\d{4}-\d{2}-\d{2}\))?")


def rel_of(path: Path) -> str | None:
    """把绝对路径转成仓库相对路径;不在课件范围内就返回 None。"""
    try:
        rel = path.resolve().relative_to(VAULT).as_posix()
    except ValueError:
        return None
    return rel if COURSE_RE.match(rel) else None


def load() -> dict:
    if COUNT_FILE.is_file():
        try:
            return json.loads(COUNT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save(data: dict) -> None:
    COUNT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True),
                          encoding="utf-8", newline="\n")


def bump(rel: str) -> dict:
    """给一次访问 +1(记首次与最近日期),返回该条记录。"""
    today = dt.date.today().isoformat()
    data = load()
    rec = data.get(rel) or {"count": 0, "first": today, "last": today}
    rec["count"] = int(rec.get("count", 0)) + 1
    rec["last"] = today
    rec.setdefault("first", today)
    data[rel] = rec
    save(data)
    return rec


def _suffix(rec: dict | None) -> str:
    if not rec:
        return ""
    return " · 进入 %d 次(最近 %s)" % (rec["count"], rec.get("last", ""))


def write_index_suffixes() -> int:
    """把次数写进各项目 `00-索引.md` 的课程块;返回改动行数。"""
    data = load()
    by_name: dict[str, dict] = {}
    for rel, rec in data.items():
        by_name[rel.rsplit("/", 1)[-1]] = rec
    changed = 0
    for index in sorted((VAULT / PROJECT_DIR).glob("*/00-索引.md")):
        lines = index.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = re.search(r"\((?:<)?(?:lessons|reference)/([^)>]+\.html)(?:>)?\)", line)
            if not m:
                continue
            base = SUFFIX_RE.sub("", line)
            new = base + _suffix(by_name.get(m.group(1)))
            if new != line:
                lines[i] = new
                changed += 1
        if changed:
            index.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return changed


def course_pages() -> list[tuple[str, str, str, str]]:
    """(项目名, 类别, 相对路径, 标题)——给首页用,现扫现读,不缓存。"""
    out = []
    base = VAULT / PROJECT_DIR
    title_re = re.compile(r"<title>(.*?)</title>", re.S | re.I)
    for proj in sorted(p for p in base.iterdir() if p.is_dir()):
        for kind in ("lessons", "reference"):
            for f in sorted((proj / kind).glob("*.html")):
                m = title_re.search(f.read_text(encoding="utf-8"))
                title = m.group(1).strip() if m else f.stem
                out.append((proj.name, kind, "%s/%s/%s" % (PROJECT_DIR, proj.name, kind + "/" + f.name), title))
    return out


if __name__ == "__main__":
    import sys
    if "--update-only" in sys.argv:
        print("已按 counts.json 更新 %d 行课程索引" % write_index_suffixes())
