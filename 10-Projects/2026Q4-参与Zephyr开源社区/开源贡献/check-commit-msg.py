#!/usr/bin/env python3
"""Zephyr 提交信息本地预检(UL2/UC1-UC6 的近似实现)。

用途:向 Zephyr / west 提 PR 前,在没有 CI 的情况下先自查提交信息是否会被
Compliance Checks 判失败。规则真源是 ci-tools 的 scripts/gitlint/
zephyr_commit_rules.py;本文件是它的等价复刻(不含 gitlint 依赖)。

用法:
    python check-commit-msg.py            # 检查 HEAD
    python check-commit-msg.py <rev>      # 检查指定提交,如 HEAD~1 或 sha
    python check-commit-msg.py --msgfile <path>   # 检查一份消息文件

退出码 0 表示全部通过。
"""

import re
import subprocess
import sys

# UC2:Signed-off-by 必须是 "两词全名 <email>"
SIGNOFF_RE = re.compile(r"(^)Signed-off-by: ([-'\w.]+) ([-'\w.]+) (.*)", re.IGNORECASE)
# UC3:标题必须是 "<subsystem>: <subject>"(Zephyr 的 .gitlint 用的近似式)
TITLE_RE = re.compile(r"^[^:]+: .+")
TITLE_MAX = 72          # UC5
BODY_MAX = 75           # UC4(注意 Ci 里配的是 75,不是默认 80)
BODY_MIN_LINES = 2      # UC6
URL_RE = re.compile(r"http[s]?://")


def read_message(rev: str) -> str:
    out = subprocess.run(
        ["git", "log", "-1", "--format=%B", rev],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.rstrip("\n")


def check(message: str) -> list[str]:
    lines = message.split("\n")
    title = lines[0]
    body = lines[1:]
    problems: list[str] = []

    if not TITLE_RE.match(title):
        problems.append(f"UC3 标题不是 '<subsystem>: <subject>' 形式: {title!r}")
    if len(title) > TITLE_MAX:
        problems.append(f"UC5 标题超长({len(title)}>{TITLE_MAX})")

    content = [ln for ln in body if ln.strip() and not ln.lower().startswith("signed-off-by")]
    if len(content) < BODY_MIN_LINES:
        problems.append(f"UC6 正文有效行不足({len(content)}<{BODY_MIN_LINES})")

    signoff_ok = False
    for ln in body:
        if ln.lower().startswith("signed-off-by"):
            if SIGNOFF_RE.search(ln):
                signoff_ok = True
            else:
                problems.append(
                    "UC2 Signed-off-by 必须是两词全名,例如 "
                    "'Signed-off-by: Chen Chen <you@example.com>';实际:" + repr(ln)
                )
    if not signoff_ok and not any(ln.lower().startswith("signed-off-by") for ln in body):
        problems.append("UC2 缺少 Signed-off-by 行(用 git commit --signoff,或在消息里手写)")

    for nr, ln in enumerate(body, start=2):
        if ln.startswith("Signed-off-by") or URL_RE.search(ln):
            continue
        if len(ln) > BODY_MAX:
            problems.append(f"UC4 第 {nr} 行超长({len(ln)}>{BODY_MAX}): {ln!r}")

    return problems


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--msgfile"]:
        message = open(args[1], encoding="utf-8").read().rstrip("\n")
        label = args[1]
    else:
        rev = args[0] if args else "HEAD"
        message = read_message(rev)
        label = rev

    problems = check(message)
    if problems:
        print(f"提交信息预检失败({label}):")
        for p in problems:
            print(" -", p)
        return 1
    print(f"提交信息预检通过({label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
