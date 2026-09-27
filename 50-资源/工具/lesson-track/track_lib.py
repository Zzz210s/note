#!/usr/bin/env python3
"""课程访问次数的计数与回写(纯本机,不用 AI、不联网)。

两个计数来源,谁也不覆盖谁:

1. **本机小服务**(`server.py`):课件经它请求时 +1 —— 精确,但要服务在跑。
2. **VS Code 集成浏览器历史**(`vscode_history.py`):你在 VS Code 里直接打开课件也算 ——
   不需要服务,但历史有条数上限,只能算**下界**。

所以记录里分开存 `service` 与 `vscode` 两个计数,`count` 取两者的**最大值**(不是相加,
避免同一次访问被两边各记一次)。`counts.json`(本机,不入库)是唯一真源;

回写:`write_index_suffixes()` 把次数追加到各项目 `00-索引.md` 课程块那一行的行尾,
先剥旧标记再写新的,所以重复跑幂等、也不会碰行里的其它字。
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


def _recount(rec: dict) -> dict:
    rec["count"] = max(int(rec.get("service", 0)), int(rec.get("vscode", 0)))
    return rec


def _new_rec(today: str) -> dict:
    return {"service": 0, "vscode": 0, "count": 0, "first": today, "last": today}


def bump(rel: str) -> dict:
    """服务收到一次课件请求:+1。"""
    today = dt.date.today().isoformat()
    data = load()
    rec = data.get(rel) or _new_rec(today)
    rec["service"] = int(rec.get("service", 0)) + 1
    rec["last"] = today
    rec.setdefault("first", today)
    data[rel] = _recount(rec)
    save(data)
    return data[rel]


def merge_history() -> dict:
    """把 VS Code 历史里的次数并进来(取最大值),返回本次变化的条数。"""
    import vscode_history
    seen = vscode_history.scan()
    today = dt.date.today().isoformat()
    data = load()
    changed = 0
    for rel, n in seen.items():
        rec = data.get(rel) or _new_rec(today)
        if int(rec.get("vscode", 0)) != n:
            rec["vscode"] = n
            rec["last"] = today
            changed += 1
        data[rel] = _recount(rec)
    save(data)
    return {"seen": len(seen), "changed": changed}


def _suffix(rec: dict | None) -> str:
    if not rec or not rec.get("count"):
        return ""
    return " · 进入 %d 次(最近 %s)" % (rec["count"], rec.get("last", ""))


def write_index_suffixes() -> int:
    """把次数写进各项目 `00-索引.md` 的课程块;返回改动行数。"""
    data = load()
    # 两张查找表:按文件名精确匹配;精确匹配不到时按「项目 + 课号」兜底
    # (课件改过名时,历史里还是旧名字 —— 0002 那次改名就是这种情形,不兜底就会丢计数。
    #  同一课号的多个历史名字会被合并求和。)
    by_name: dict[str, dict] = {}
    by_num: dict[tuple[str, str], dict] = {}
    for rel, rec in data.items():
        parts = rel.split("/")
        name = parts[-1]
        proj = parts[1] if len(parts) > 2 else ""
        num = name.split("-", 1)[0]
        by_name[name] = rec
        slot = by_num.setdefault((proj, num), {"count": 0, "last": rec.get("last", "")})
        slot["count"] += int(rec.get("count", 0))
        if rec.get("last", "") > slot.get("last", ""):
            slot["last"] = rec["last"]
    changed = 0
    for index in sorted((VAULT / PROJECT_DIR).glob("*/00-索引.md")):
        lines = index.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = re.search(r"\((?:<)?(?:lessons|reference)/([^)>]+\.html)(?:>)?\)", line)
            if not m:
                continue
            name = m.group(1)
            rec = by_name.get(name) or by_num.get((index.parent.name, name.split("-", 1)[0]))
            new = SUFFIX_RE.sub("", line) + _suffix(rec)
            if new != line:
                lines[i] = new
                changed += 1
        if changed:
            index.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return changed


def course_pages() -> list[tuple[str, str, str, str]]:
    """(项目名, 类别, 相对路径, 标题)——给首页用,现扫现读,不缓存。"""
    out = []
    title_re = re.compile(r"<title>(.*?)</title>", re.S | re.I)
    for proj in sorted(p for p in (VAULT / PROJECT_DIR).iterdir() if p.is_dir()):
        for kind in ("lessons", "reference"):
            for f in sorted((proj / kind).glob("*.html")):
                m = title_re.search(f.read_text(encoding="utf-8"))
                title = m.group(1).strip() if m else f.stem
                out.append((proj.name, kind, "%s/%s/%s/%s" % (PROJECT_DIR, proj.name, kind, f.name), title))
    return out


def sync() -> str:
    """合并历史 + 回写索引,返回一句人话总结(给命令行与首页共用)。"""
    m = merge_history()
    n = write_index_suffixes()
    return "历史里看到 %d 个课件,更新 %d 条记录;索引改动 %d 行" % (m["seen"], m["changed"], n)


if __name__ == "__main__":
    print(sync() if "--sync" in __import__("sys").argv else
          "已按 counts.json 更新 %d 行课程索引" % write_index_suffixes())
