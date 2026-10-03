#!/usr/bin/env python3
"""0-Note 在线阅读站 · 保守压缩(内联 CSS / JS 去注释与行首空白)。

只做三件事,**绝不做**变量名压缩 / 换行合并(那会破坏 ASI 与可读性):
  1. 去块注释 `/* … */`(只在字符串外删;跨行注释补一个换行,保护 ASI;行内注释补一个空格,
     避免 `a/*c*/b` 这类把两个 token 粘成一个)
  2. 去行首缩进(字符串 / 模板字面量内部的空白原样保留)
  3. 去空行与行尾空白

**行内 `//` 绝不处理**:字符串里的 `"http://a//b"` / `'// not a comment'` 必须原样保留
(见 `selftest_minify.py` 的负向用例)。

正则字面量按启发式识别(前一个有效字符属于表达式起始集 `( , = : [ ! & | ? ; { } + - * % < > ~ ^`),
整段(含字符类里的引号)原样搬 —— 否则 `/(["\\\\])/g` 里的 `"` 会让引号状态跑偏,
后续块注释就删不掉了(实测会漏 65/67 条)。

`node --check` 通过由 `selftest_minify.py` 用真实段落逐段验证。
"""
from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

__all__ = ["strip", "minify_css", "minify_js"]

REGEX_AFTER = set("(,=:[!&|?{};+-*%<>~^")


def strip(src: str) -> str:
    """一次扫描:跟踪字符串 / 正则状态,只删字符串外的块注释与行首空白。"""
    out: list[str] = []
    i, n = 0, len(src)
    quote = ""           # 当前字符串定界符:" ' ` 或空
    esc = False          # 字符串内刚读到反斜杠
    has_content = False  # 当前行是否已有非空白内容(用于丢空行 / 丢缩进)
    prev = ""            # 上一个有效字符(判断 `/` 是正则还是除号)
    while i < n:
        c = src[i]
        if quote:                                   # 字符串内:原样搬,只维护状态
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == quote:
                quote = ""
            if c == "\n":
                has_content = True                 # 多行字符串里的空行有意义,不丢
            i += 1
            continue
        if c in "\"'`":
            quote = c
            out.append(c)
            has_content = True
            prev = c
            i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            end = src.find("*/", i + 2)
            seg = src[i:] if end < 0 else src[i:end + 2]
            i = n if end < 0 else end + 2
            while out and out[-1] in " \t":
                out.pop()
            if "\n" in seg:                          # 跨行注释:补换行,ASI 不变
                if has_content:
                    out.append("\n")
                has_content = False
            elif has_content:                        # 行内注释:补空格,防 token 粘连
                out.append(" ")
            continue
        if c == "/" and i + 1 < n and src[i + 1] not in "/*" and (not prev or prev in REGEX_AFTER):
            j = i + 1                                # 正则字面量:整段原样搬
            in_class = False
            res_esc = False
            out.append(c)
            while j < n:
                d = src[j]
                out.append(d)
                if res_esc:
                    res_esc = False
                elif d == "\\":
                    res_esc = True
                elif d == "[":
                    in_class = True
                elif d == "]":
                    in_class = False
                elif d == "/" and not in_class:
                    j += 1
                    break
                elif d == "\n":
                    break
                j += 1
            while j < n and src[j].isalpha():        # 正则 flags
                out.append(src[j])
                j += 1
            has_content = True
            prev = ")"
            i = j
            continue
        if c == "\n":
            while out and out[-1] in " \t":
                out.pop()
            if has_content:
                out.append("\n")
            has_content = False
            i += 1
            continue
        if c in " \t" and not has_content:           # 行首缩进:丢
            i += 1
            continue
        out.append(c)
        if c not in " \t":
            has_content = True
            prev = c
        i += 1
    return "".join(out)


def minify_css(src: str) -> str:
    """CSS 内联压缩:去块注释 + 行首缩进 + 空行。"""
    return strip(src)


def minify_js(src: str) -> str:
    """JS 内联压缩:同上;行内 `//` 原样保留。"""
    return strip(src)
