#!/usr/bin/env python3
"""teach-links.py —— 名词课之间的联动检测(只读,不改文件)。

判据两条:
  1) **该链却没链**:课 A 的“正文”(剥掉 HTML 标签,并排除页头 .lesson-meta 与 <footer>)
     里出现了课 B 的关键词,但正文里没有指向 B 的 <a href="NNNN-….html">。
     关键词表单一是下面的 KEYWORDS —— 要新增课就改这一处。
  2) **单向联动**:课 A 的**正文**里链了课 B,而 B 的正文没链回 A。
     页头「前置」与页脚「下一节预告」是天然有向的指针(先读 / 下一节),不参与这条判据。

用法:
  python -B teach-links.py                # 全量报告
  python -B teach-links.py --only 0011    # 只看与 0011 有关的条目
  python -B teach-links.py --quiet        # 只打汇总(给验收用)
  python -B teach-links.py --keywords     # 附打印关键词表
退出码:0 = 无待办且无单向;1 = 有待办(便于接进验收)。
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
LESSONS = VAULT / "10-项目" / "!名词解释" / "lessons"

# 单一真源:课程文件名主干 -> 该课的关键词(命中即说明这一节被别处提到)
KEYWORDS: dict[str, tuple[str, ...]] = {
    "0001-CLI,TUI,GUI": ("CLI", "TUI", "GUI", "命令行界面", "图形用户界面", "字符界面", "终端模拟器"),
    "0002-编辑器,编译器,解释器,IDE": ("编辑器", "编译器", "解释器", "IDE", "JIT", "字节码"),
    "0003-时间复杂度与空间复杂度": ("时间复杂度", "空间复杂度", "大 O", "大O", "O(n)"),
    "0004-Node.js,npm,pnpm": ("Node.js", "npm", "pnpm", "npx", "yarn", "corepack", "包管理器"),
    "0005-测试夹具": ("测试夹具", "夹具", "fixture", "mock", "stub", "断言"),
    "0006-巡检器": ("巡检器", "一致性检查", "linter", "退出码"),
    "0007-UI与UX": ("UI", "UX", "交互设计", "可访问性", "WCAG"),
    "0008-CI,CD": ("CI", "CD", "持续集成", "持续交付", "持续部署", "workflow"),
    "0009-路由模式与桥接模式": ("路由模式", "桥接模式", "NAT", "桥接", "拨号", "光猫"),
    "0010-Wayland": ("Wayland", "X11", "合成器", "显示服务器"),
    "0011-tmux": ("tmux", "终端复用器", "GNU screen", "nohup", "伪终端", "pty", "SIGHUP", "detach", "接回"),
    "0012-GRUB": ("GRUB", "引导加载程序", "bootloader", "UEFI", "固件", "启动菜单", "initramfs"),
    "0013-前端,后端,接口": ("API", "全栈"),
    "0014-Kubernetes": ("Kubernetes", "K8s", "容器编排", "编排器", "Pod"),
    "0015-Gradle": ("Gradle", "构建工具", "增量构建", "任务图", "Maven"),
    "0016-静态部署与其它部署": ("静态部署", "静态托管", "客户端渲染", "缓存失效", "CDN"),
    "0017-SSG": ("SSG", "静态站点生成", "服务端渲染", "SSR", "水合", "预渲染"),
    "0018-树莓派": ("树莓派", "单板计算机", "GPIO"),
    "0019-SaaS": ("SaaS", "IaaS", "PaaS", "多租户", "订阅制", "软件即服务"),
    "0020-抓包": ("抓包", "Wireshark", "tcpdump", "pcap", "会话重组"),
    "0021-爬虫": ("爬虫", "robots", "屏幕抓取", "去重"),
}

SCRIPT = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
HEADER = re.compile(r'<p class="lesson-meta">.*?</p>', re.S)
FOOTER = re.compile(r"<footer>.*?</footer>", re.S)
TAG = re.compile(r"<[^>]+>")
HREF = re.compile(r'href="(\d{4}-[^"#]+)\.html(?:#[^"]*)?"')
CJK = re.compile(r"[\u3000-\u9fff\uff00-\uffef]")
BOUND = r"(?<![0-9A-Za-z_]){}(?![0-9A-Za-z_])"


def body_html(raw: str) -> str:
    """剥掉脚本/样式、页头元信息、页脚,保留其余标签(用来查正文里的链接)。"""
    return FOOTER.sub(" ", HEADER.sub(" ", SCRIPT.sub(" ", raw)))


def plain(raw: str) -> str:
    return html.unescape(TAG.sub(" ", body_html(raw)))


def pattern(kw: str) -> re.Pattern[str]:
    """纯 ASCII 关键词按词边界匹配(否则 UI 会在 GUI、build 里命中)。"""
    esc = re.escape(kw)
    return re.compile(BOUND.format(esc) if not CJK.search(kw) else esc, re.I)


def sentence(text: str, pos: int, width: int = 40) -> str:
    start = max(text.rfind(ch, 0, pos) for ch in "。！？!?\n") + 1
    ends = [i for i in (text.find(ch, pos) for ch in "。！？!?\n") if i != -1]
    chunk = re.sub(r"\s+", " ", text[start:min(ends) if ends else len(text)]).strip()
    return chunk[:width] + "…" if len(chunk) > width else chunk


def load(directory: Path) -> dict[str, dict[str, str]]:
    out = {}
    for path in sorted(directory.glob("*.html")):
        raw = path.read_text(encoding="utf-8")
        out[path.stem] = {"raw": raw, "body": plain(raw), "links": body_html(raw)}
    return out


def scan(lessons: dict[str, dict[str, str]]) -> list[dict]:
    rows = []
    for stem, data in lessons.items():
        body = data["body"]
        linked = set(HREF.findall(data["links"]))
        for target, kws in KEYWORDS.items():
            if target == stem or target not in lessons or target in linked:
                continue
            found = []
            for kw in kws:
                hits = list(pattern(kw).finditer(body))
                if hits:
                    found.append((kw, len(hits), hits[0].start()))
            if found:
                first = min(found, key=lambda f: f[2])
                rows.append({
                    "stem": stem, "target": target,
                    "kws": [(kw, n) for kw, n, _ in found],
                    "count": sum(n for _, n, _ in found),
                    "where": sentence(body, first[2]),
                })
    return rows


def edge_map(lessons: dict[str, dict[str, str]]) -> dict[str, set[str]]:
    """正文级联动边(页头前置 / 页脚预告不算 —— 它们天生有向)。"""
    return {s: set(HREF.findall(d["links"])) & set(lessons) - {s} for s, d in lessons.items()}


def one_way(edges: dict[str, set[str]]) -> list[tuple[str, str]]:
    return [(a, b) for a in sorted(edges) for b in sorted(edges[a]) if a not in edges[b]]


def keep(pair: tuple[str, str], only: str | None) -> bool:
    return not only or any(x.startswith(only) for x in pair)


def main() -> int:
    ap = argparse.ArgumentParser(description="名词课联动检测(只读)")
    ap.add_argument("--quiet", action="store_true", help="只打汇总")
    ap.add_argument("--only", metavar="前缀", help="只看与某节课有关的条目,如 0011")
    ap.add_argument("--keywords", action="store_true", help="附打印关键词表")
    ap.add_argument("--dir", default=str(LESSONS), help="课程目录(自检时指向假库)")
    args = ap.parse_args()

    lessons = load(Path(args.dir))
    rows = [r for r in scan(lessons) if keep((r["stem"], r["target"]), args.only)]
    pairs = [p for p in one_way(edge_map(lessons)) if keep(p, args.only)]

    if not args.quiet:
        if args.keywords:
            print("关键词表(单一真源 KEYWORDS):")
            for stem, kws in KEYWORDS.items():
                print(f"  {stem}: {' / '.join(kws)}")
            print()
        print(f"名词课联动检测 · {len(lessons)} 节课 · 关键词表 {len(KEYWORDS)} 组")
        print(f"\n待办(正文命中关键词却没有正文链接):{len(rows)} 条")
        for r in rows:
            kws = "、".join(f"{kw}×{n}" for kw, n in r["kws"])
            print(f"  {r['stem']}\n    -> {r['target']}  共 {r['count']} 处 · 词:{kws}")
            print(f"       首次出现:{r['where']}")
        print(f"\n单向联动(A 链了 B,B 没链 A):{len(pairs)} 条")
        for a, b in pairs:
            print(f"  {a} -> {b}")
    print(f"汇总:待办 {len(rows)} 条 · 单向联动 {len(pairs)} 条"
          + (f" · 过滤 --only {args.only}" if args.only else ""))
    return 1 if rows or pairs else 0


if __name__ == "__main__":
    sys.exit(main())
