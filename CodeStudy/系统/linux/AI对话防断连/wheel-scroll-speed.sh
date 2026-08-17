#!/usr/bin/env bash
# pi 全屏模式滚轮速度补丁:每格滚动行数 1 -> 默认 3(可用环境变量 PI_WHEEL_SCROLL_LINES 覆盖)
# 解决:tmux 容器内滚轮翻阅上下文卡顿(每事件只滚 1 行,远程往返多导致的迟滞感)
# 重新应用场景:pi update / pi update self 之后重跑本脚本。
set -euo pipefail

TUI="/usr/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-tui/dist/tui-alt-screen.js"

sudo python3 - "$TUI" <<'EOF'
import sys
path = sys.argv[1]
src = open(path).read()
old = "this.wheelScrollLines = Math.max(1, Math.floor(options.wheelScrollLines ?? 1));"
new = ("const wheelDefault = Number.parseInt(process.env.PI_WHEEL_SCROLL_LINES ?? \"3\", 10);\n"
       "        this.wheelScrollLines = Math.max(1, Math.floor(options.wheelScrollLines ?? (Number.isFinite(wheelDefault) && wheelDefault > 0 ? wheelDefault : 3)));")
if new in src:
    print("tui-alt-screen: already patched")
elif src.count(old) == 1:
    open(path, "w").write(src.replace(old, new))
    print("tui-alt-screen: patched")
else:
    sys.exit("tui-alt-screen: pattern not found (pi 版本可能已变,需手动检查)")
EOF

node --check "$TUI" && echo "syntax OK - 完成(重启 pi 会话后生效;PI_WHEEL_SCROLL_LINES=n 可调)"
