#!/usr/bin/env python3
"""site_counts.py 自检:种子内容 / 转义 / 序列化键 / 前端契约 / 合并口径 / join。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note/50-资源/工具/site-build && python -B selftest_counts.py

口径:种子键是**仓库相对路径**,页面侧标识是 **slug**,两者不能直接相等,
join 一律走 `entry["path"]`(实现见 `site_counts.bake`,见 test_bake_join_by_path);
喂给页面的序列化器必须输出 slug 键(见 test_serializer_keys_are_slugs,拿真库清单验证)。
JS 行为打桩在 `selftest_counts_js.py`,由本文件的 main() 一并汇总执行。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import selftest_counts_js as JS
import site_counts as C
import site_scan

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


def test_seed_json_plain_keeps_path_keys():
    """不传 entries 时仍是种子原文(路径键)—— 这种形态只能看,不能内联给前端。"""
    assert json.loads(C.seed_json()) == C.load_seed(), "无参形态应等于种子原文"
    assert CLI in json.loads(C.seed_json()), "无参形态的键仍是路径"


def test_serializer_keys_are_slugs():
    """页面口径:传 entries 时序列化键 == bake() 的键,且形如 slug(真库跑)。"""
    entries = site_scan.scan("public")
    baked = C.bake(entries)
    sj = C.seed_json(entries)
    assert "</script>" not in sj and "<" not in sj, "带 entries 也必须转义 `<`"
    keys = set(json.loads(sj))
    assert keys == set(baked), "序列化键必须与 bake 键一致(%s vs %s)" % (sorted(keys), sorted(baked))
    assert keys, "真库 public 清单应有种子命中"
    assert not any(k.endswith(".html") or "/" in k for k in keys), "键不得是路径:%s" % sorted(keys)
    assert set(json.loads(C.seed_json())) != keys, "键不得等同于种子原文的路径键"
    assert any(k.startswith("0001-") for k in keys), "缺 0001 的 slug 键:%s" % sorted(keys)


def test_bake_ignores_non_dict_seed_value():
    """种子值被手改成非 dict 时按缺省丢弃,不得 AttributeError 崩掉生成器。"""
    seed = {CLI: 5, RETIRED: {"count": 1}}
    entries = [{"path": CLI, "slug": "0001-CLI-TUI-GUI"},
               {"path": RETIRED, "slug": "retired-card"}]
    out = C.bake(entries, seed)
    assert list(out) == ["retired-card"], out
    assert out["retired-card"] == {"count": 1, "first": "", "last": ""}, out


def test_missing_seed_returns_empty():
    """负向:种子文件缺失时返回空表并提示一行,不抛异常。"""
    orig = C.SEED_PATH
    C.SEED_PATH = Path(orig).with_name("__no_such_counts_seed__.json")
    try:
        assert C.load_seed() == {}, "缺文件应返回空表"
    finally:
        C.SEED_PATH = orig


def main() -> int:
    fns = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    fns += [v for k, v in vars(JS).items() if k.startswith("test_") and callable(v)]
    fns.sort(key=lambda f: f.__name__)
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
