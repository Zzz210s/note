#!/usr/bin/env python3
"""0-Note 巡检扩展:A11 教学工作区完整性(teach 技能的状态层)。

2026-09-24 起,`10-项目/` 下每个学习项目都是一个 `teach` 教学工作区,状态层至少要有:

- `MISSION.md`    为什么学 / 成功长什么样 / 约束 / 不做什么
- `RESOURCES.md`  可信资源清单(Knowledge / Wisdom / Gaps)

这两份文件按技能协议用英文名,且**豁免** A3 孤篇、A5/A6 元数据、A7 项目产出计数
(见 `vault_lib.is_teach_scaffold`)—— 它们是技能状态,不是库内笔记。缺了就没人守,
所以单独用 A11 兜:缺文件、或文件被写成空壳(缺章节)都报。

`GLOSSARY.md` / `lessons/` / `reference/` / `assets/` / `learning-records/` 按技能要求
**按需创建**(术语表只在用户真的掌握某个词之后才加),所以 A11 不要求它们存在。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_lib as L

# 每个文件必须出现的章节标题(空壳防线:文件在、内容是占位,也算没建)
REQUIRED = {
    "MISSION.md": ("## Why", "## Success looks like", "## Constraints", "## Out of scope"),
    "RESOURCES.md": ("## Knowledge", "## Gaps"),
}


def check_teach_workspace() -> list[L.Finding]:
    """A11:每个学习项目(有 `!项目说明.md` 的项目目录)必须是一个可用的教学工作区。"""
    out: list[L.Finding] = []
    root = L.VAULT_ROOT / "10-项目"
    if not root.exists():
        return out
    for proj in sorted(p for p in root.iterdir() if p.is_dir()):
        if not (proj / "!项目说明.md").exists():
            continue          # 追踪区等非学习项目(无项目说明)不在管辖范围
        rel_proj = L.rel_path(proj)
        for name, sections in REQUIRED.items():
            f = proj / name
            if not f.exists():
                out.append(L.Finding("A11", rel_proj, 0, "缺 %s(教学工作区状态层)" % name))
                continue
            text = L.read_text(f)
            missing = [s for s in sections if s not in text]
            if missing:
                out.append(L.Finding("A11", L.rel_path(f), 0,
                                     "缺章节 %s(疑似空壳)" % " / ".join(missing)))
    return out
