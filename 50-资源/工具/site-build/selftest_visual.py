#!/usr/bin/env python3
"""工作台视觉自检(headless 实测):组件尺寸与三态,按拾枝规则核对(设计 spec §5)。

与 `selftest_tokens.py` 分工:那张表读**源码字符串**(刻度、令牌、态是否写了),
这张表开真 `index.html` 读**计算样式**(尺寸/圆角/阴影/悬停底色是否真生效)。

单跑:`PYTHONIOENCODING=utf-8 python -B selftest_visual.py`
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROME = ("C:/Users/23652/AppData/Local/ms-playwright/chromium_headless_shell-1228/"
          "chrome-headless-shell-win64/chrome-headless-shell.exe")
PAGE = "F:/0-Note/index.html"
PUPPETEER = "C:/Users/23652/AppData/Roaming/npm/node_modules/puppeteer-core"

PROBE = r"""
const puppeteer = require(process.env.PP);
const EXE = process.env.CHROME, URL = process.env.PAGE;
(async () => {
  const b = await puppeteer.launch({ executablePath: EXE, args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const p = await b.newPage();
  await p.setViewport({ width: 1280, height: 860 });
  await p.goto(URL, { waitUntil: 'load', timeout: 180000 });
  await p.evaluate(() => localStorage.clear());
  await p.reload({ waitUntil: 'load', timeout: 180000 });
  await new Promise(r => setTimeout(r, 900));
  const base = await p.evaluate(() => {
    const g = s => document.querySelector(s);
    const cs = s => { const e = g(s); return e ? getComputedStyle(e) : null; };
    const box = s => { const e = g(s); if (!e) return null; const r = e.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; };
    let sb = null;
    for (const ss of document.styleSheets) {
      try { for (const r of ss.cssRules) if (r.cssText && r.cssText.indexOf('::-webkit-scrollbar{') >= 0 && r.cssText.indexOf('width:10px') >= 0) sb = '10px'; } catch (e) {}
    }
    return {
      cardRadius: cs('.proj-card') && cs('.proj-card').borderRadius,
      cardShadow: cs('.proj-card') && cs('.proj-card').boxShadow,
      cardBg: cs('.proj-card') && cs('.proj-card').backgroundColor,
      chipRadius: cs('.chip') && cs('.chip').borderRadius,
      chipH: box('.chip') && box('.chip').h,
      chipBg: cs('.chip') && cs('.chip').backgroundColor,
      iconBtn: box('.icon-btn') && box('.icon-btn').h,
      inputH: box('#side-q') && box('#side-q').h,
      scrollbar: sb,
    };
  });
  await p.hover('.proj-card');
  await new Promise(r => setTimeout(r, 300));
  const cardBgHover = await p.evaluate(() => getComputedStyle(document.querySelector('.proj-card')).backgroundColor);
  await p.click('.tree[data-group=course] .tree-item');
  await new Promise(r => setTimeout(r, 900));
  const opened = await p.evaluate(() => {
    const g = s => document.querySelector(s);
    const cs = s => { const e = g(s); return e ? getComputedStyle(e) : null; };
    const box = s => { const e = g(s); if (!e) return null; const r = e.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; };
    return {
      tabH: box('.tab') && box('.tab').h,
      tabActiveBg: cs('.tab[aria-selected=true]') && cs('.tab[aria-selected=true]').backgroundColor,
      tabIdleBg: cs('.tab[aria-selected=false]') && cs('.tab[aria-selected=false]').backgroundColor,
      tabRadius: cs('.tab-cell') && cs('.tab-cell').borderRadius,
      frameShadow: cs('.group-body[data-kind=lesson]') && cs('.group-body[data-kind=lesson]').boxShadow,
    };
  });
  console.log(JSON.stringify({ ...base, ...opened, cardBgHover }));
  await b.close();
})();
"""


def run_probe() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        f = pathlib.Path(tmp) / "probe.cjs"
        f.write_text(PROBE, encoding="utf-8")
        env = dict(os.environ, PP=PUPPETEER, CHROME=CHROME, PAGE=PAGE)
        out = subprocess.run(["node", str(f)], capture_output=True, text=True,
                             encoding="utf-8", env=env, timeout=300)
    if out.returncode != 0:
        raise SystemExit("headless 探针失败:\n%s" % (out.stderr or out.stdout)[-800:])
    return json.loads(out.stdout.strip().splitlines()[-1])


def main() -> int:
    r = run_probe()
    passed = failed = 0

    def ok(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print("PASS", name)
        else:
            failed += 1
            print("FAIL", name, detail)

    ok("卡片圆角 = 8px(拾枝 r-card)", r["cardRadius"] == "8px", r["cardRadius"])
    ok("卡片无阴影(chrome 靠边框分,只有浮层用阴影)", r["cardShadow"] in ("none", ""), r["cardShadow"])
    ok("卡片悬停底色变化", r["cardBg"] != r["cardBgHover"], "%s → %s" % (r["cardBg"], r["cardBgHover"]))
    ok("chip 圆角 = 4px", r["chipRadius"] == "4px", r["chipRadius"])
    ok("chip 高 ∈ [20,22]", r["chipH"] is not None and 20 <= r["chipH"] <= 22, str(r["chipH"]))
    ok("chip 默认中性底(chrome 白)", r["chipBg"] == "rgb(255, 255, 255)", r["chipBg"])
    ok("标签页高 = 32px(含 1px 下边框时 31)", r["tabH"] in (31, 32), str(r["tabH"]))
    ok("活动标签底色 != 非活动标签", r["tabActiveBg"] != r["tabIdleBg"],
       "%s vs %s" % (r["tabActiveBg"], r["tabIdleBg"]))
    ok("标签圆角 = 6px(6/6/0/0)", r["tabRadius"].startswith("6px"), r["tabRadius"])
    ok("图标按钮高 = 28px", r["iconBtn"] == 28, str(r["iconBtn"]))
    ok("侧栏搜索框高 = 32px", r["inputH"] == 32, str(r["inputH"]))
    ok("内嵌课容器无阴影", r["frameShadow"] in ("none", ""), r["frameShadow"])
    print("结论:%s(%d 例,%d 失败)" % ("PASS" if not failed else "FAIL", passed + failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
