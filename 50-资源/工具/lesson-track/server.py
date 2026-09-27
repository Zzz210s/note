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
import json
import re
import sys
import threading
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import track_lib as T
import watch as W
from watch import watch_forever
from http_handler import Handler
import rename_by_count as R

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="本机课程访问计数服务")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--update-only", action="store_true", help="只按 counts.json 回写索引后退出")
    ap.add_argument("--ensure", action="store_true",
                    help="若端口已被占用则直接退出 0(给 VS Code 的 folderOpen 任务用,重复启动不报错)")
    args = ap.parse_args(argv)
    if args.ensure:
        import socket
        probe = socket.socket()
        busy = probe.connect_ex(("127.0.0.1", args.port)) == 0
        probe.close()
        if busy:
            print("课程服务已在运行(端口 %d),本次不重复启动。" % args.port)
            return 0
    if args.update_only:
        print("已更新课程索引 %d 行" % T.write_index_suffixes())
        return 0
    print("启动时同步一次:")
    print("  " + T.sync())
    print("课程服务已启动:http://127.0.0.1:%d/" % args.port)
    print("在 VS Code 里用 Simple Browser 打开上面这个地址;Ctrl+C 停止。")
    threading.Thread(target=watch_forever, daemon=True).start()
    print("守望已启动:每 %d 秒合并一次 VS Code 历史,计数变了就按次数改名。" % W.WATCH_INTERVAL)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
