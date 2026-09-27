#!/usr/bin/env python3
"""后台守望:合并 VS Code 历史 + 在"课件被关掉"之后按次数改名。

用户口径(2026-09-27):**关掉课件才算读完一次**。所以:
- 主路径:页面在关闭那一刻发 `/closed` 给服务(`lesson-close-beacon.js`),服务调 `rename_now()`;
- 兜底:VS Code 历史里最后一次出现已超过 `CLOSE_GRACE_MS`,当作已经关掉(`watch_forever` 里的判断);
- 两个途径都不动别人的文件:只改课件名与其引用(见 `rename_by_count.py`)。
"""
from __future__ import annotations

import threading
import time

import rename_by_count as R
import track_lib as T

LAST_REWRITE = 0.0
LAST_RENAME = 0.0
LOCK = threading.Lock()
WATCH_INTERVAL = 10      # 秒:多久合并一次 VS Code 历史
CLOSE_GRACE_MS = 120_000  # 兜底阈值:历史里最后一次出现已经过了这么久,就当它被关掉了
AUTO_COMMIT = True       # 改名后自动提交(只提交自己改过的路径)

def maybe_rewrite(force: bool = False) -> None:
    """定期把 VS Code 历史里的次数并进 counts.json;默认最多每 10 秒一次。"""
    global LAST_REWRITE
    with LOCK:
        if not force and time.time() - LAST_REWRITE < 10:
            return
        LAST_REWRITE = time.time()
    try:
        print("  ↳ " + T.sync())
    except Exception as e:  # 索引更新失败不能影响读课
        print("  ↳ 索引更新失败:", e)


def rename_now() -> None:
    """有课被关掉就立刻按次数改名(带节流,避免连点几个页面时反复改名)。"""
    global LAST_RENAME
    with LOCK:
        if time.time() - LAST_RENAME < 2:
            return
        LAST_RENAME = time.time()
    try:
        plan = R.build_plan()
        if plan:
            res = R.apply_plan(plan, do_commit=AUTO_COMMIT)
            print("  ↳ 按次数改名 %d 个课件(改了 %d 个文件里的引用%s)"
                  % (res["renamed"], len(res["refs"]), ",已提交" if res["committed"] else ""))
    except Exception as e:
        print("  ↳ 改名出错:", e)


def _closed_enough(rec: dict) -> bool:
    """这一节是不是"可以算读完了":页面上报过关闭,或者历史里最后一次出现已超过宽限期。"""
    if int(rec.get("closed", 0)) > 0:
        return True
    last_ms = int(rec.get("hist_last_ms", 0))
    return bool(last_ms) and (time.time() * 1000 - last_ms) > CLOSE_GRACE_MS


def watch_forever() -> None:
    """后台守望:每 10 秒合并一次 VS Code 历史;计数有变化就按次数改名。

    "关掉课件就更新"就是这么实现的 —— 页面关掉后,VS Code 的历史里多了一条记录,
    下一轮守望就能看到,于是改名并同步全库引用。改名与引用改写都只发生在我们自己的文件上。
    """
    while True:
        time.sleep(WATCH_INTERVAL)
        try:
            T.merge_history()
            data = T.load()
            plan = R.build_plan()
            # 用户口径:关掉课件才算读完 —— 所以只改名"确实关掉了"的那些(见 _closed_enough)
            ready = {f: dst for f, dst in plan.items()
                     if _closed_enough(data.get(T.norm_key(f.relative_to(T.VAULT).as_posix()), {}))}
            if ready:
                res = R.apply_plan(ready, do_commit=AUTO_COMMIT)
                print("  ↳ 按次数改名 %d 个课件(改了 %d 个文件里的引用%s)"
                      % (res["renamed"], len(res["refs"]), ",已提交" if res["committed"] else ""))
        except Exception as e:      # 守望出错绝不能拖垮服务
            print("  ↳ 守望出错:", e)

