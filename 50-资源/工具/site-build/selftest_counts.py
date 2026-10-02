#!/usr/bin/env python3
"""site_counts.py 自检:种子内容 / 转义 / 前端契约 / 合并口径 / join。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note/50-资源/工具/site-build && python -B selftest_counts.py

口径:种子键是**仓库相对路径**,页面侧标识是 **slug**,两者不能直接相等,
join 一律走 `entry["path"]`(实现见 `site_counts.bake`,本自检第 6 例)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import site_counts as C

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RETIRED = "10-项目/!名词解释/reference/路由与桥接速查.html"
CLI = "10-项目/!名词解释/lessons/0001-CLI,TUI,GUI.html"


def test_seed_contents():
    """种子里 0001 是 2 次;条数 >= 5;已退役的速查卡键不存在。"""
    seed = C.load_seed()
    assert CLI in seed, "缺 0001 的种子键"
    assert seed[CLI]["count"] == 2, seed[CLI]
    assert len(seed) >= 5, len(seed)
    assert RETIRED not in seed, "退役速查卡不得留在种子里"
    for rec in seed.values():
        assert set(rec) >= {"count", "first", "last"}, rec


def test_seed_json_escaping():
    """内联 JSON 里不能有裸 `<`(防 `</script>` 提前闭合脚本)。"""
    sj = C.seed_json()
    assert "</script>" not in sj, "出现了裸 </script>"
    assert "<" not in sj, "所有 `<` 都必须转义成 \\u003c"
    assert json.loads(sj) == C.load_seed(), "转义不得改变数据"


def test_counts_js_contract():
    """前端契约:localStorage 键 note:counts;旧 beacon 方案不得回潮。"""
    js = C.COUNTS_JS
    assert "note:counts" in js, "缺 localStorage 键"
    assert "localStorage" in js, "缺 localStorage 读写"
    assert "lesson-close-beacon" not in js, "旧回报器不得回潮"
    assert "window.__counts" in js, "必须导出 window.__counts"
    for name in ("get", "inc", "clear"):
        assert name in js, "缺方法 " + name


def test_merge_arithmetic():
    """显示 = 烘焙 + 增量:必须出现相加表达式,且 get 里不得自增。"""
    js = C.COUNTS_JS
    assert "+ (rec.add" in js, "缺 烘焙 + 增量 的相加表达式"
    get_body = js[js.index("function get("):js.index("function inc(")]
    assert "inc(" not in get_body, "get 里不得自增(自增由工作台调 inc)"


def test_clear_only_increment():
    """clear 只把本地增量归零,不碰烘焙值。"""
    js = C.COUNTS_JS
    body = js[js.index("function clear("):js.index("window.__counts")]
    assert "{add:0}" in body, "clear 应写成 {add:0} 形态"
    assert "SEED" not in body and "baked" not in body, "clear 不得改烘焙值"


def test_bake_join_by_path():
    """join 走 entry.path:种子里有、条目清单里没有的键必须被丢弃。"""
    seed = {
        "10-项目/!名词解释/lessons/0001-CLI,TUI,GUI.html": {"count": 2, "first": "2026-09-27", "last": "2026-09-27"},
        "10-项目/!名词解释/reference/路由与桥接速查.html": {"count": 1, "first": "2026-09-27", "last": "2026-09-27"},
    }
    entries = [{"path": "10-项目/!名词解释/lessons/0001-CLI,TUI,GUI.html",
                "slug": "0001-CLI-TUI-GUI"}]
    out = C.bake(entries, seed)
    assert list(out) == ["0001-CLI-TUI-GUI"], out
    assert out["0001-CLI-TUI-GUI"]["count"] == 2, out


def test_missing_seed_returns_empty():
    """负向:种子文件缺失时返回空表并提示一行,不抛异常。"""
    orig = C.SEED_PATH
    C.SEED_PATH = Path(orig).with_name("__no_such_counts_seed__.json")
    try:
        assert C.load_seed() == {}, "缺文件应返回空表"
    finally:
        C.SEED_PATH = orig


def main() -> int:
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print("FAIL", fn.__name__, "->", exc)
        else:
            print("PASS", fn.__name__)
    if failed:
        print("结论:FAIL(%d/%d)" % (failed, len(fns)))
        return 1
    print("结论:PASS(%d)" % len(fns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
