#!/usr/bin/env python3
"""从 VS Code 集成浏览器(Simple Browser)的历史里数出「每节课件进了几次」。

已实测(2026-09-27):VS Code 把用 Simple Browser 打开过的地址记在

    %APPDATA%\\Code\\User\\globalStorage\\state.vscdb       键 browser.history.entries.global
    %APPDATA%\\Code\\User\\workspaceStorage\\<hash>\\state.vscdb   (按工作区)

每条是 `{id, url, time, title}`,**保留重复** —— 同一节课开两次就是两条,所以能数出次数。
好处:不需要任何常驻服务,只要你在 VS Code 里打开过课件,这里就有记录。

两个诚实的限制:
- 这份历史**有条数上限**(旧条目会被挤掉),所以它是"至少进过这么多次"的**下界**;
  因此计数取 `max(服务计数, 历史计数)`,不会把两边相加。
- 它只认识 **file://(或 127.0.0.1 服务)** 形式的课件地址;历史库被锁时读取会失败,
  那种情况返回空字典,不报错。
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import sqlite3
import tempfile
import urllib.parse
from collections import Counter

import re
import shutil

VAULT = pathlib.Path(__file__).resolve().parents[3]
COURSE_RE = re.compile(r"^10-项目/[^/]+/(lessons|reference)/[^/]+\.html$")
HISTORY_KEYS = ("browser.history.entries.global", "browser.history.entries")
APP_DIRS = ("Code", "Code - Insiders", "VSCodium", "Cursor")


def _state_dbs() -> list[pathlib.Path]:
    """VS Code 家族的状态库(全局 + 各工作区)。"""
    appdata = pathlib.Path(os.environ.get("APPDATA", ""))
    out: list[pathlib.Path] = []
    for app in APP_DIRS:
        user = appdata / app / "User"
        if not user.is_dir():
            continue
        g = user / "globalStorage" / "state.vscdb"
        if g.is_file():
            out.append(g)
        ws = user / "workspaceStorage"
        if ws.is_dir():
            out.extend(sorted(ws.glob("*/state.vscdb")))
    return out


def _read_items(db_path: pathlib.Path) -> list[dict]:
    """把历史条目读出来。库被占用时先复制一份再读(Windows 上直接开常常失败)。"""
    tmp = pathlib.Path(tempfile.gettempdir()) / ("vscode-hist-%d.vscdb" % abs(hash(str(db_path))))
    try:
        shutil.copy2(db_path, tmp)
    except Exception:
        return []
    items: list[dict] = []
    try:
        db = sqlite3.connect(str(tmp))
        for key in HISTORY_KEYS:
            row = db.execute("select value from ItemTable where key=?", (key,)).fetchone()
            if not row or not row[0]:
                continue
            try:
                data = json.loads(row[0])
            except Exception:
                continue
            got = data.get("items", data if isinstance(data, list) else [])
            items.extend(x for x in got if isinstance(x, dict) and "url" in x)
        db.close()
    except Exception:
        return []
    finally:
        tmp.unlink(missing_ok=True)
    return items


def _rel_from_url(url: str) -> str | None:
    """把历史里的 URL 换成仓库相对路径;不是课件的返回 None。"""
    raw = urllib.parse.unquote(url.split("?", 1)[0].split("#", 1)[0])
    low = raw.lower()
    if low.startswith("file://"):
        rest = raw[7:]
        # Windows 上 file:///f:/0-Note/... 会多一个前导斜杠,去掉它
        if re.match(r"^/[a-zA-Z]:", rest):
            rest = rest[1:]
        candidate = pathlib.Path(rest)
    elif low.startswith(("http://127.0.0.1", "http://localhost")):
        m = re.match(r"^https?://(?:127\.0\.0\.1|localhost)(?::\d+)?/(.*)$", raw, re.I)
        if not m:
            return None
        candidate = VAULT / m.group(1)
    else:
        return None

    try:
        rel = candidate.resolve().relative_to(VAULT.resolve()).as_posix()
    except ValueError:
        # 盘符大小写/斜杠写法不一致时,按小写前缀再比一次
        c = candidate.as_posix().lower().lstrip("/")
        v = VAULT.as_posix().lower().lstrip("/")
        if not c.startswith(v + "/"):
            return None
        rel = candidate.as_posix().lstrip("/")[len(v) + 1:]
    return rel if COURSE_RE.match(rel) else None


def scan() -> dict[str, int]:
    """返回 {课件相对路径: 历史里出现过的次数}。"""
    counter: Counter[str] = Counter()
    for db in _state_dbs():
        for it in _read_items(db):
            rel = _rel_from_url(str(it.get("url", "")))
            if rel:
                counter[rel] += 1
    return dict(counter)


if __name__ == "__main__":
    got = scan()
    print("VS Code 历史里能对上的课件:%d 个" % len(got))
    for rel, n in sorted(got.items(), key=lambda x: -x[1]):
        print("  %2d 次  %s" % (n, rel))
