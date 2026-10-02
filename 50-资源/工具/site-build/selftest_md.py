#!/usr/bin/env python3
"""site_md.py 自检:逐条核对简报里的 10 类语法 + 边界。

跑法(Windows 必须带 PYTHONIOENCODING=utf-8):
  cd F:/0-Note/50-资源/工具/site-build && python -B selftest_md.py

口径:简报第 1 条正文写 `<h1>标题</h1>`,随后括号又写「h1 也降级为 h2」,
设计文档 §5 的正文层级(H1 -> h2)为准 —— 这里断言 `<h2>标题</h2>`。
"""
from __future__ import annotations

import sys

import site_md as M

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def test_headings():
    """源文 H1 降为 h2,其余顺延一级(源 H2 -> h3),最多 h6。"""
    assert M.render_md("# 标题") == "<h2>标题</h2>"
    assert M.render_md("## 二级") == "<h3>二级</h3>"
    assert M.render_md("###### 六级") == "<h6>六级</h6>"


def test_paragraphs():
    """空行分段;段内软换行合并(两侧都是 CJK 时不插空格)。"""
    assert M.render_md("甲\n\n乙") == "<p>甲</p><p>乙</p>"
    assert M.render_md("甲\n乙") == "<p>甲乙</p>"          # CJK 之间不插空格
    assert M.render_md("a\nb") == "<p>a b</p>"            # 非 CJK 维持原样


def test_lists():
    """`- ` 是无序,`1. ` 是有序;连续行合成一个列表。"""
    assert M.render_md("- a\n- b") == "<ul><li>a</li><li>b</li></ul>"
    assert M.render_md("1. b\n2. c") == "<ol><li>b</li><li>c</li></ol>"
    assert M.render_md("- a\n\n1. b") == "<ul><li>a</li></ul><ol><li>b</li></ol>"


def test_table():
    """三行表格(表头 / 分隔 / 数据)-> thead + tbody。"""
    html = M.render_md("| a | b |\n| --- | --- |\n| 1 | 2 |")
    assert html.startswith("<table><thead>"), html
    assert "<th>a</th><th>b</th>" in html, html
    assert "<tbody><tr><td>1</td><td>2</td></tr></tbody>" in html, html


def test_fence():
    """围栏内 `#` 不是标题、`<b>` 被转义,整体进 `<pre><code>`。"""
    html = M.render_md("```\n# 不是标题\n<b>不转义</b>\n```")
    assert "<pre><code>" in html and "</code></pre>" in html, html
    assert "# 不是标题" in html, html
    assert "&lt;b&gt;不转义&lt;/b&gt;" in html, html
    assert "<h2>" not in html and "<b>" not in html, html


def test_inline_code():
    """行内代码里的 `*` / `#` 不被当语法。"""
    html = M.render_md("看 `a*b*c` 和 `# 井号`")
    assert "<code>a*b*c</code>" in html, html
    assert "<code># 井号</code>" in html, html
    assert "<em>" not in html, html


def test_bold_and_link():
    html = M.render_md("**粗** 与 [文字](http://x)")
    assert "<strong>粗</strong>" in html, html
    assert '<a href="http://x">文字</a>' in html, html
    # 库里的写法:`[名](<../路径/文件.md>)`(URL 两端用尖括号包住)
    html2 = M.render_md("[项目](<../10-项目/!名词解释/00-索引.md>)")
    assert '<a href="../10-项目/!名词解释/00-索引.md">项目</a>' in html2, html2
    assert "&lt;" not in html2, html2


def test_html_escape():
    """原始 HTML 一律转义;`&` 也要转。"""
    html = M.render_md("<script>alert(1)</script> A & B")
    assert "&lt;script&gt;" in html and "&lt;/script&gt;" in html, html
    assert "<script>" not in html, html
    assert "A &amp; B" in html, html


def test_quote_and_hr():
    assert "<blockquote><p>引用</p></blockquote>" in M.render_md("> 引用")
    assert "<hr>" in M.render_md("---")


def test_wikilink_injected():
    """给了 known 映射:命中生成锚点,未命中退化成纯文字(不产 `<a>`)。"""
    known = {"tmux": "0011-tmux"}
    html = M.render_md("[[tmux]] / [[路径/其它|显示]]", known=known)
    assert '<a class="wl" href="#0011-tmux">tmux</a>' in html, html
    assert "显示" in html, html
    assert "其它" not in html, html          # 找不到目标,只留显示文字
    assert html.count("<a ") == 1, html


def test_wikilink_real_vault():
    """默认 known 取自真库:课标题 tmux 应链到它的条目 slug。"""
    import site_scan as S
    ent = next(e for e in S.scan("all") if e["title"] == "tmux")
    html = M.render_md("见 [[tmux]]。")
    assert 'href="#%s"' % ent["slug"] in html, html


def test_edge_cases():
    """空输入 / 只有 frontmatter / 未闭合围栏都不崩,且无占位符残留。"""
    assert M.render_md("") == ""
    assert M.render_md("---\ntitle: x\n---") == ""
    assert "未闭合 &lt;x&gt;" in M.render_md("```\n未闭合 <x>")
    assert "\x00" not in M.render_md("`c`\n\n```\ncode\n```")


def test_image_degrades():
    """`![alt](url)` 整个退化为纯文字 alt(不留 `!`、不留链接)。"""
    assert M.render_md("![图](http://a/b.png)") == "<p>图</p>"
    html = M.render_md("![单词表截图](<../../../50-资源/x.png>)")
    assert html == "<p>单词表截图</p>", html


def test_link_scheme_whitelist():
    """危险协议退化为纯文字;http/https/mailto/#/相对路径放行且 href 必带引号。"""
    for u in ("javascript:window.location='/evil'", "JavaScript:alert",
              "data:text/html,payload", "vbscript:msgbox"):
        html = M.render_md("[x](%s)" % u)
        assert html == "<p>x</p>", (u, html)
    for u in ("http://a", "https://a", "mailto:a@b", "#anchor", "../a/b.md", "a.md"):
        html = M.render_md("[x](%s)" % u)
        assert '<a href="%s">x</a>' % u in html, (u, html)


def test_link_attribute_injection():
    """URL 里的引号不得逃出 href(不产生 onmouseover 等事件属性)。"""
    html = M.render_md('[x](<http://a" onmouseover="location=\'//evil\'">)')
    assert "onmouseover" not in html, html
    assert '"' not in html, html                 # 所有引号都转义成 &quot;


def test_link_code_token_injection():
    """行内代码占位符混进 URL 时不产生新属性(整条退化为纯文字)。"""
    html = M.render_md('[x](http://a`" onmouseover="alert(1)"`)')
    assert "onmouseover" not in html, html
    assert "<a " not in html, html


def test_wikilink_anchor():
    """`[[目标#锚点]]` 先切掉 `#…` 查表;命中出锚点,未命中不留 `#` 碎片。"""
    known = {"tmux": "0011-tmux"}
    assert '<a class="wl" href="#0011-tmux">tmux</a>' in M.render_md(
        "[[tmux#安装]]", known=known)
    html = M.render_md("[[不存在#安装]]", known=known)
    assert "#" not in html and "安装" not in html, html


def test_italic_guard():
    """`*` 后紧跟空白不当强调(`2 * 3 * 4` 不产 `<em>`)。"""
    assert "<em>" not in M.render_md("2 * 3 * 4 = 24")
    assert "<em>斜</em>" in M.render_md("*斜*")


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
