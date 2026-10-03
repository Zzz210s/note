#!/usr/bin/env python3
"""0-Note 在线阅读站 · 扫描器。

`git ls-files` -> 条目清单(分类 / frontmatter / 标题 / 摘要 / slug / 正文)。
数据源只用 `git ls-files`(不用 os.walk):未入库的 `50-资源/` 素材与 AI 产物天然不会漏进站。

对外集合 public = `*/lessons/*.html` ∪ `*/20-知识/*.md` ∪ `50-资源/记录/*.md`
(记录并入笔记,`kind` 仍是 note、另带 `is_record=True` 供渲染层给「记录」徽章);
全库 all = 全部已跟踪 md + html。课(lesson)只取标题与 `.win`,body 为 None;
课内可搜索正文(去 <script>/<style> 与标签)由 `site_search.entry_text` 现读现算,
此处 `chars` 也用同一口径的 `html_doc_text`,不再把脚本/样式计入长度。
纯文本工具见 `site_scan_lib`(slug / frontmatter / 摘要),此处从它转出公开接口。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from site_scan_lib import (clip, first_content, first_paragraph, h1, html_doc_text,
                           html_paragraph, html_text, parse_frontmatter, slugify)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 本文件在 <仓库根>/50-资源/工具/site-build/,故 parents[3] = 仓库根(同 vault_lib)
VAULT_ROOT = Path(__file__).resolve().parents[3]

SCAFFOLD_FILES = {"MISSION.md", "RESOURCES.md", "NOTES.md", "!项目说明.md", "!实施计划.md"}
TYPE_DEFAULT = {"index": "索引", "scaffold": "脚手架"}

TITLE_TAG = re.compile(r"<title>(.*?)</title>", re.S)
DESC_TAG = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.S)
WIN_DIV = re.compile(r'<div class="win">(.*?)</div>', re.S)  # 非贪婪:当前 `.win` 内无嵌套 div,将来若嵌套会在首个 </div> 处截断
LESSON_META = re.compile(r'<p class="lesson-meta">(.*?)</p>', re.S)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
COURSE_CODE = re.compile(r"^(?:x\d+-)?\d+$")   # 课号:`0011`(兼容旧 `x<n>-` 前缀)


def _git_ls(*globs: str) -> list[str]:
    """已跟踪文件清单(-z 免转义,兼容中文与空格路径)。"""
    out = subprocess.run(["git", "ls-files", "-z", *globs], cwd=VAULT_ROOT, capture_output=True)
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0") if p]


def _section(rel: str) -> str:
    """条目所属节:`10-项目/<项目>` 取项目名,其余取目录(根级文件归 `根目录`)。"""
    parts = rel.split("/")
    if parts[0] == "10-项目" and len(parts) > 1:
        return parts[1]
    if parts[0] == "50-资源" and len(parts) > 1:
        return "50-资源/" + parts[1]
    return parts[0] if parts[0] in ("00-索引", "90-模板") else "根目录"


def _md_kind(rel: str) -> str:
    base = rel.rsplit("/", 1)[-1]
    if base == "00-索引.md":
        return "index"
    return "scaffold" if base in SCAFFOLD_FILES else "note"


def _page_title(tag: str) -> str:
    """课/参考页 <title> -> 标题。

    课约定为 `课号 · 名称 · 工作区`(如 `0011 · tmux · 名词解释`)→ 去末段工作区、
    再去课号,只留名称;参考页只有 `名称 · 工作区`(如 `课程地图 · Docker(容器化)`),
    两段整体保留。
    """
    parts = [p.strip() for p in tag.strip().split("·") if p.strip()]
    if len(parts) >= 3:
        parts = parts[:-1]
        if len(parts) >= 2 and COURSE_CODE.match(parts[0]):
            parts = parts[1:]
    return " · ".join(parts) or tag.strip()


def _md_entry(rel: str) -> dict:
    text = (VAULT_ROOT / rel).read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    kind = _md_kind(rel)
    title = h1(body) or Path(rel).stem
    return {
        "kind": kind,
        "path": rel,
        "title": title,
        "slug": Path(rel).stem,
        "section": _section(rel),
        "type": fm.get("type") or TYPE_DEFAULT.get(kind, "笔记"),
        "status": fm.get("status", ""),
        "date": fm.get("date", ""),
        "tags": fm.get("tags", []),
        "related": fm.get("related", []),
        "is_record": rel.startswith("50-资源/记录/"),
        "summary": clip(first_paragraph(body) or first_content(body) or title),
        "body": body,
        "win": None,
        "chars": len(body),
    }


def _html_entry(rel: str) -> dict:
    text = (VAULT_ROOT / rel).read_text(encoding="utf-8", errors="replace")
    lesson = "/lessons/" in rel
    title_tag = TITLE_TAG.search(text)
    win_match = WIN_DIV.search(text)
    win = html_text(win_match.group(1)) if win_match else ""
    desc = DESC_TAG.search(text)
    meta = LESSON_META.search(text)
    dates = DATE.findall(meta.group(1)) if meta else []
    return {
        "kind": "lesson" if lesson else "note",
        "path": rel,
        "title": _page_title(title_tag.group(1)) if title_tag else Path(rel).stem,
        "slug": Path(rel).stem,
        "section": _section(rel),
        "type": "tutorial" if lesson else "reference",
        "status": "",
        "date": dates[-1] if dates else "",
        "tags": [],
        "related": [],
        "is_record": False,
        "summary": clip((desc.group(1) if desc else "") or win or html_paragraph(text)),
        "body": None,
        "win": win or None,
        "chars": len(html_doc_text(text)),
    }


def _build_entries() -> list[dict]:
    entries: list[dict] = []
    for rel in sorted(_git_ls()):
        if rel.endswith(".md"):
            entries.append(_md_entry(rel))
        elif rel.endswith(".html"):
            entries.append(_html_entry(rel))
    used: set[str] = set()
    for e in entries:
        base = slugify(e["slug"])
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        e["slug"] = slug
    return entries


def scan(mode: str) -> list[dict]:
    """mode='public' 返回对外集合(课 + 20-知识 + 记录);mode='all' 返回全库。"""
    entries = _build_entries()
    if mode == "all":
        return entries
    if mode == "public":
        return [e for e in entries
                if e["kind"] == "lesson"
                or (e["kind"] == "note"
                    and ("/20-知识/" in e["path"] or e.get("is_record")))]
    raise ValueError(f"mode 只能是 public / all,收到 {mode!r}")
