#!/usr/bin/env python3
"""site_md 的安全与文本辅助:HTML 转义 + URL 白名单 + 中文软换行合并。

拆成独立模块只为让 `site_md.py` 保持在 200 行以内(库规),两者无循环依赖。
"""
from __future__ import annotations

import re


def esc(s: str) -> str:
    """HTML 转义四种危险字符(先 `&` 再 `<` `>` `"`);`"` 防属性逃逸。"""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


_SCHEME = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):")
_OK_SCHEMES = frozenset({"http", "https", "mailto"})
# URL 里出现这些就不安全:引号会逃出 href;尖括号 / 反引号 / 占位符 NUL 会被当标记
_UNSAFE_URL = re.compile(r"[\x00\"<>`]|&(?:quot|lt|gt);")
# CJK(含全角标点、假名):软换行两侧都是它时不插空格
_CJK = re.compile(
    r"[\u2e80-\u303f\u3040-\u30ff\u3400-\u4dbf"
    r"\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")


def safe_url(url: str) -> str | None:
    """`href` 白名单:http/https/mailto、`#` 锚点、相对路径。

    其余(尤其 javascript:/data:/vbscript:,忽略大小写)返回 None,调用方
    退化成纯链接文字;含引号 / 尖括号 / 反引号 / NUL 的 URL 同样拒绝。
    """
    u = url.strip()
    if not u or _UNSAFE_URL.search(u):
        return None
    if u.startswith("#"):
        return u
    m = _SCHEME.match(u)
    return None if (m and m.group(1).lower() not in _OK_SCHEMES) else u


def soft_join(parts: list[str]) -> str:
    """合并软换行:两侧都是 CJK 时不插空格,其余照旧插一个空格。"""
    out = parts[0] if parts else ""
    for p in parts[1:]:
        gap = "" if out and p and _CJK.match(out[-1]) and _CJK.match(p[0]) else " "
        out += gap + p
    return out
