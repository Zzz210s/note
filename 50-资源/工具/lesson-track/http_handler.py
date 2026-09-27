#!/usr/bin/env python3
"""课程服务的 HTTP 层:静态托管仓库根 + 计数 + 首页。

计数三处:
- `GET` 到课件 → `T.bump()`(服务口径);
- `POST /closed` → `T.bump_close()`(**读完一次的主口径**,页面关闭时上报)+ 立刻改名;
- `GET /counts.json` → 给页面/调试看原始数据(放行跨源,便于 file:// 页面读取)。
"""
from __future__ import annotations

import html
import json
import threading
from http.server import SimpleHTTPRequestHandler

import track_lib as T
import watch as W

def render_home() -> bytes:
    counts = T.load()
    pages = T.course_pages()
    groups: dict[str, dict[str, list]] = {}
    for proj, kind, rel, title in pages:
        groups.setdefault(proj, {"lessons": [], "reference": []})[kind].append((rel, title))
    total = sum(len(v["lessons"]) for v in groups.values())
    rows = []
    for proj in sorted(groups):
        g = groups[proj]
        rows.append("<section class=\"drill\"><h2>%s</h2>" % html.escape(proj))
        for kind, label in (("lessons", "课程"), ("reference", "速查卡")):
            if not g[kind]:
                continue
            rows.append("<h3>%s(%d)</h3><ul>" % (label, len(g[kind])))
            for rel, title in g[kind]:
                rec = counts.get(rel) or counts.get(T.norm_key(rel))
                mark = ("<strong>进入 %d 次</strong>(最近 %s)" % (rec["count"], rec.get("last", ""))
                        if rec else "<span style=\"color:#999\">还没进过</span>")
                rows.append('<li><a href="/%s">%s</a> — %s</li>' % (html.escape(rel), html.escape(title), mark))
            rows.append("</ul>")
        rows.append("</section>")
    body = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>课程首页 · 0-Note</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/90-模板/teach-assets/lesson.css">
</head><body>
<p class="lesson-meta">本机课程入口 · 全部 %d 节课 · 点击即计数 · 数据只在你这台机器上</p>
<h1>课程首页</h1>
<p>下面按项目列出全部课件。<strong>点进去就算一次</strong>,次数会写回各项目的
<code>00-索引.md</code>(最多每分钟一次),也会显示在这里。</p>
%s
</body></html>
""" % (total, "\n".join(rows))
    return body.encode("utf-8")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(T.VAULT), **kw)

    def do_POST(self):  # noqa: N802
        if self.path.split("?")[0] == "/closed":
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n).decode("utf-8", "ignore") if n else ""
            rel = None
            try:
                rel = (json.loads(raw) or {}).get("rel")
            except Exception:
                rel = raw.strip() or None
            if rel:
                rel2 = T.norm_key(rel)
                rec = T.bump_close(rel2)
                print("  ← 关闭:%s → 读完 %d 次" % (rel2.rsplit("/", 1)[-1], rec["count"]))
                threading.Thread(target=W.rename_now, daemon=True).start()
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):  # noqa: N802(标准库命名)
        if self.path in ("/", "/index.html"):
            W.maybe_rewrite(force=True)
            body = render_home()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/counts.json":
            body = T.COUNT_FILE.read_bytes() if T.COUNT_FILE.is_file() else b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            # 课件是 file:// 打开的,要让它们能读到这份数据必须放行跨源
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        raw = urllib.parse.unquote(self.path.split("?")[0]).lstrip("/")
        rel = T.rel_of(T.VAULT / raw)
        if rel:
            rec = T.bump(rel)
            print("  %s → 进入 %d 次" % (rel.split("/")[-1], rec["count"]))
            threading.Thread(target=W.maybe_rewrite, daemon=True).start()
        super().do_GET()

    def log_message(self, fmt, *args):  # 默认日志太吵,只留一行精简输出
        if "code 404" in (fmt % args):
            print("  404:", self.path)

