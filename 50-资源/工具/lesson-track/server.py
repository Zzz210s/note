#!/usr/bin/env python3
"""课程访问计数小服务(纯 Python 标准库,不联网、不用 AI)。

用法(在仓库任意位置):
    PYTHONIOENCODING=utf-8 python -B 50-资源/工具/lesson-track/server.py
然后在 VS Code 里用 Simple Browser(命令面板:Simple Browser: Show)打开

    http://127.0.0.1:8787/

首页按项目列出**全部课件**(lessons 与 reference),每条后面写着「进入 N 次」;
点进去就算一次,次数写进 `counts.json`,并顺手把次数回写到各项目 `00-索引.md` 的课程块
(最多每分钟一次,避免每次点击都去改文件)。

为什么需要一个小服务:静态 HTML 页面没有权限写你磁盘上的索引;要让"点一次就加一次"成立,
计数必须发生在**请求经过的那个进程**里 —— 也就是这里。
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import threading
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import track_lib as T

LAST_REWRITE = 0.0
LOCK = threading.Lock()


def maybe_rewrite(force: bool = False) -> None:
    """把次数回写到索引;默认最多每 10 秒一次(首页会强制刷一次)。"""
    global LAST_REWRITE
    with LOCK:
        if not force and time.time() - LAST_REWRITE < 10:
            return
        LAST_REWRITE = time.time()
    try:
        print("  ↳ " + T.sync())
    except Exception as e:  # 索引更新失败不能影响读课
        print("  ↳ 索引更新失败:", e)


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
                rec = counts.get(rel)
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

    def do_GET(self):  # noqa: N802(标准库命名)
        if self.path in ("/", "/index.html"):
            maybe_rewrite(force=True)
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
            threading.Thread(target=maybe_rewrite, daemon=True).start()
        super().do_GET()

    def log_message(self, fmt, *args):  # 默认日志太吵,只留一行精简输出
        if "code 404" in (fmt % args):
            print("  404:", self.path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="本机课程访问计数服务")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--update-only", action="store_true", help="只按 counts.json 回写索引后退出")
    args = ap.parse_args(argv)
    if args.update_only:
        print("已更新课程索引 %d 行" % T.write_index_suffixes())
        return 0
    print("启动时同步一次:")
    print("  " + T.sync())
    print("课程服务已启动:http://127.0.0.1:%d/" % args.port)
    print("在 VS Code 里用 Simple Browser 打开上面这个地址;Ctrl+C 停止。")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
