#!/usr/bin/env python3
"""Zephyr/RST 单文件本地预检(docutils + 交叉引用 + 标题下划线)。

Zephyr 的文档构建(doctrees + doxygen + twister 生成内容)在 Windows 上很重,
而且前面有 CI 队列。这个脚本用 docutils 直接在单个 .rst 上做结构检查,再补两项
Sphinx 才知道的事情:`:ref:` 目标是否存在、标题下划线是否够长。

用法:
    python check-rst.py <file.rst> [--root <仓库根目录>]

Sphinx 专有项(`:ref:`、`:file:`、`.. code-block::` 等)注册为空实现,因此它们的
"unknown role/directive" 报错不会算作问题;真正的结构错误(标题层级、缩进、
列表、表格)会被报出来。

退出码 0 表示通过。
"""

import argparse
import pathlib
import re
import sys

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive, directives, roles

SPHINX_ROLES = (
    "ref", "doc", "file", "envvar", "kconfig", "option", "command",
    "program", "guilabel", "menuselection", "kbd", "samp", "abbr",
    "numref", "term", "download", "zephyr_file",
)
SPHINX_DIRECTIVES = (
    "code-block", "toctree", "literalinclude", "image", "figure", "note",
    "warning", "tip", "important", "deprecated", "versionadded",
    "versionchanged", "glossary", "doxygenstruct", "doxygenfunction",
    "doxygengroup", "table", "csv-table", "list-table", "rubric", "hint",
)


def _dummy_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    return [nodes.literal(rawtext, text)], []


class _DummyDirective(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 99
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        return []


def register_sphinx_stubs() -> None:
    for name in SPHINX_ROLES:
        roles.register_local_role(name, _dummy_role)
    for name in SPHINX_DIRECTIVES:
        directives.register_directive(name, _DummyDirective)


def structure_problems(path: pathlib.Path) -> list[str]:
    register_sphinx_stubs()
    source = path.read_text(encoding="utf-8")
    problems: list[str] = []
    doctree = publish_doctree(
        source,
        settings_overrides={"report_level": 2, "halt_level": 5, "warning_stream": open("nul", "w")},
    )
    for msg in doctree.findall(nodes.system_message):
        if msg.get("level", 0) >= 2:
            problems.append(f"docutils L{msg.get('level')} line={msg.get('line')}: {msg.astext().splitlines()[0][:120]}")
    return problems


def split_literal_problems(path: pathlib.Path) -> list[str]:
    """内联字面量(``...``)跨行时,换行会被原样渲染进输出,而 Sphinx 不会给警告。

    判据:某行里 `` 的出现次数是奇数,就说明有一个字面量从上一行延续过来。
    code-block 里的内容是字面文本,跳过。
    """
    problems = []
    literal_indent: int | None = None
    for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), start=1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if literal_indent is not None:
            if not stripped or indent > literal_indent:
                continue
            literal_indent = None
        if re.match(r"^\s*\.\. code-block::", line):
            literal_indent = indent
            continue
        if line.count("``") % 2 == 1:
            problems.append(f"内联字面量跨行(行 {i}): {stripped[:70]!r}")
    return problems


def underline_problems(path: pathlib.Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").split("\n")
    problems = []
    for i in range(len(lines) - 1):
        title, under = lines[i], lines[i + 1]
        if not title.strip() or title.startswith("..") or title.startswith(".. "):
            continue
        if re.fullmatch(r"[*#=\-~^+]{3,}", under.strip()) and len(under.rstrip()) < len(title.rstrip()):
            problems.append(f"标题下划线过短(行 {i + 1}): {title!r}")
    return problems


def ref_problems(path: pathlib.Path, root: pathlib.Path | None) -> list[str]:
    if root is None:
        return []
    text = path.read_text(encoding="utf-8")
    wanted = set(re.findall(r":ref:`[^`<]*<([^`>]+)>`", text)) | set(re.findall(r":ref:`([a-z0-9][a-z0-9_-]+)`", text))
    if not wanted:
        return []
    defined = set()
    for rst in root.rglob("*.rst"):
        if ".git" in rst.parts:
            continue
        for m in re.finditer(r"^\.\. _([^:\s]+):", rst.read_text(encoding="utf-8", errors="ignore"), re.MULTILINE):
            defined.add(m.group(1))
    return [f":ref: 目标不存在: {label}" for label in sorted(wanted - defined)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--root", default=None, help="仓库根目录,用于检查 :ref: 目标是否存在")
    args = ap.parse_args()

    path = pathlib.Path(args.file)
    if not path.is_file():
        print(f"文件不存在: {path}")
        return 2

    root = pathlib.Path(args.root).resolve() if args.root else None
    problems = (
        structure_problems(path)
        + split_literal_problems(path)
        + underline_problems(path)
        + ref_problems(path, root)
    )
    if problems:
        print(f"RST 预检失败({path}):")
        for p in problems:
            print(" -", p)
        return 1
    print(f"RST 预检通过({path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
