#!/usr/bin/env python3
"""`build_site.py` 的自检:三条断言真会拦、正常路径真能出文件。

用例(全部在系统临时目录里跑,不碰仓库):
  1. 正常构建 -> rc 0,两页都写出,且卡片数 == 条目数
  2. 条目被截断(monkeypatch `site_scan.scan`) -> rc 1 且**不写出文件**
  3. 页面里混进 `<script src=` -> 断言 2 报错
  4. 体量超门槛 -> 断言 3 报错
  5. 输出原子性:断言失败时不留下 `.tmp`
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import build_site
import site_scan

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = FAIL = 0


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS", name)
    else:
        FAIL += 1
        print("FAIL", name, detail)


def run(modes, out: Path) -> int:
    argv = sys.argv
    sys.argv = ["build_site.py"] + modes + ["--out-dir", str(out)]
    try:
        return build_site.main()
    except SystemExit as e:          # 断言失败会 SystemExit(1),自检要拿它当返回值
        return int(e.code or 0)
    finally:
        sys.argv = argv


def main() -> int:
    real_scan = site_scan.scan
    with tempfile.TemporaryDirectory() as d:
        out = Path(d)
        # 1. 正常构建
        rc = run(["--public", "--all"], out)
        ok("正常构建 rc=0", rc == 0, "rc=%s" % rc)
        for name in ("index.html", "all.html"):
            p = out / name
            ok("%s 已写出" % name, p.exists() and p.stat().st_size > 100_000)
        pub = (out / "index.html").read_text(encoding="utf-8")
        ok("卡片数 == 对外条目数", pub.count('class="card"') == len(real_scan("public")),
           "%d vs %d" % (pub.count('class="card"'), len(real_scan("public"))))

        # 2. 条目截断 -> 必须 rc 1 且不写出
        out2 = out / "trunc"
        out2.mkdir()
        site_scan.scan = lambda mode: real_scan(mode)[:-1] if mode == "public" else real_scan(mode)
        rc = run(["--public"], out2)
        site_scan.scan = real_scan
        ok("截断条目 rc=1", rc == 1, "rc=%s" % rc)
        ok("截断时不写出文件", not (out2 / "index.html").exists() and not list(out2.glob("*.tmp")))

        # 3. 外部资源 -> 断言 2 报错
        entries = real_scan("public")
        page = "<script src=\"x.js\"></script>" + "<link rel=\"stylesheet\" href=\"a.css\">"
        errs = build_site.check("public", entries, page)
        ok("外部资源被拦", any("外部资源" in e for e in errs), str(errs))

        # 4. 体量超门槛 -> 断言 3 报错
        big = "x" * (build_site.GATES["public"] + 10)
        errs = build_site.check("public", entries, big)
        ok("超体量被拦", any("体量" in e for e in errs), str(errs))

        # 5. 原子性:失败后无 .tmp 残留
        ok("无 .tmp 残留", not list(out.glob("*.tmp")))

    print("结论:%s(%d 例,%d 失败)" % ("PASS" if FAIL == 0 else "FAIL", PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
