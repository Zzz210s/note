#!/usr/bin/env python3
"""site_search.py 自检:课内正文与笔记全文都进索引,片段不越界。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note/50-资源/工具/site-build && python -B selftest_search.py

口径(设计 §5 与验收 V1):41 节课的 `text` 都非空且合计 ≥120000;搜「伪终端 / 前缀键 /
SIGHUP」各 ≥1 条(这三个词只出现在课件正文里);笔记不再截 600 字;`snippet()` 的负向
(不命中返回空串、命中在首尾不越界)与 `script`/`style` 块真被丢掉。
"""
from __future__ import annotations

import sys

import site_scan
import site_scan_lib as L
import site_search as S

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = FAIL = 0
WORDS = ("伪终端", "前缀键", "SIGHUP")


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS", name)
    else:
        FAIL += 1
        print("FAIL", name, detail)


def test_lesson_text_full():
    """课内正文全量进索引:每节非空、合计够大(设计实测去标签 149 KB,留余量)。"""
    idx = S.build_index(site_scan.scan("public"))
    lessons = [e for e in idx if e["kind"] == "course"]
    empty = [e["anchor"] for e in lessons if not e["text"].strip()]
    ok("每节课 text 非空", bool(lessons) and not empty, "课 %d · 空 %s" % (len(lessons), empty[:3]))
    total = sum(len(e["text"]) for e in lessons)
    ok("课 text 合计 ≥120000", total >= 120000, "合计 %d" % total)


def test_keywords_hit():
    """三个只在课件正文里出现的词必须能搜到。"""
    idx = S.build_index(site_scan.scan("public"))
    for w in WORDS:
        n = sum(1 for e in idx if w in e["text"] or w in e["title"])
        ok("搜「%s」≥1 条" % w, n >= 1, "%d 条" % n)


def test_note_full_text():
    """笔记:索引文本 >600,且正文末尾一段话真在索引里(证明没被截断)。"""
    pub = site_scan.scan("public")
    idx = {e["anchor"]: e for e in S.build_index(pub)}
    pick = None
    for e in pub:
        if e["kind"] != "note" or not e.get("body"):
            continue
        full = S.md_doc_text(e["body"])
        if len(full) > 600:
            pick = (e, full)
            break
    ok("存在长笔记(>600)", pick is not None)
    if pick is None:
        return
    e, full = pick
    text = idx[e["slug"]]["text"]
    ok("长笔记 text >600", len(text) > 600, "len=%d" % len(text))
    tail = [ln for ln in e["body"].splitlines() if L.clean_inline(ln)]
    probe = L.clean_inline(tail[-1])[-8:] if tail else ""
    ok("正文尾部一段话在索引里", bool(probe) and probe in text, "probe=%r" % probe)


def test_snippet_bounds():
    """snippet 负向:不命中 -> 空串;命中在首尾不越界。"""
    ok("不命中返回空串", S.snippet("abc def", "zzz") == "")
    ok("空 term 返回空串", S.snippet("abc", "") == "")
    head = S.snippet("term 后面还有字", "term", width=3)
    ok("命中在开头", head == "term 后面", repr(head))
    tail_t = "前面有字 term"
    tail = S.snippet(tail_t, "term", width=3)
    ok("命中在结尾", tail == "有字 term", repr(tail))
    full = S.snippet("短", "短", width=30)
    ok("宽度大于文本", full == "短", repr(full))


def test_entry_text_clean():
    """课:无标签残留、script/style 块丢掉;笔记:无围栏与强调标记。"""
    idx = {e["anchor"]: e for e in S.build_index(site_scan.scan("public"))}
    lesson = next(e for e in idx.values() if e["kind"] == "course")
    ok("课 text 无 <> ", "<" not in lesson["text"] and ">" not in lesson["text"])
    spun = S.html_doc_text('<p>正文</p><script>var secret=1;</script><style>.a{}</style>')
    ok("script/style 块被丢掉", spun == "正文" and "secret" not in spun and ".a{}" not in spun, repr(spun))
    note = next(e for e in idx.values() if e["kind"] in ("know", "project") and e["text"])
    ok("笔记 text 无围栏与 **", "```" not in note["text"] and "**" not in note["text"])


def main() -> int:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]:
        fn()
    print("结论:%s(%d 例,%d 失败)" % ("PASS" if FAIL == 0 else "FAIL", PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
