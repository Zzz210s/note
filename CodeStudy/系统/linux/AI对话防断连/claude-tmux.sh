# Claude Code auto-tmux protection
# 安装位置：~/.claude-tmux.sh，由 ~/.bashrc 末尾 source。
# 作用：让交互式 `claude` 跑在「每项目一个」的持久 tmux 会话里，
#       使其在 SSH 掉线 / VS Code 关闭后依然存活。
# 重连：在同一项目目录再敲 `claude`，或 `tmux a -t <session>`。
# 停用：注释掉 ~/.bashrc 里的 source 行。

# 按项目目录推导会话名。slot=1 为 cc-<目录名>-<cksum4>（无后缀，向后兼容）；
# slot>1 追加 -N，使同一目录可并行跑多个 claude（如 `claude 2`、`claude 3`）。
_claude_tmux_session_name() {
  local pwd="${1:-$PWD}" slot="${2:-1}"
  (( slot < 1 )) && slot=1
  local name="cc-$(basename "${pwd:-/}")-$(printf '%s' "$pwd" | cksum | cut -c1-4)"
  name="${name//[^A-Za-z0-9_-]/_}"
  (( slot > 1 )) && name="${name}-${slot}"
  printf '%s' "$name"
}

claude() {
  # 可选数字槽位：`claude 2`、`claude 3` ... -> 同目录不同会话。
  # 在此消费掉，不会传给 claude。
  local slot=1
  if [[ ${1:-} =~ ^[0-9]+$ ]]; then
    slot=$1; shift
    (( slot < 1 )) && slot=1
  fi

  # 只保护交互式入口；其余（-p/--print、MCP、config、update、doctor 等）原样透传。
  case "${1:-}" in
    ""|-c|--continue|-r|--resume)
      ;;
    *)
      command claude "$@"
      return $?
      ;;
  esac

  # 已在 tmux 内 -> 直接运行，不嵌套。
  if [ -n "$TMUX" ]; then
    command claude "$@"
    return $?
  fi

  # 未装 tmux -> 回退为裸 claude。
  if ! command -v tmux >/dev/null 2>&1; then
    command claude "$@"
    return $?
  fi

  local sname
  sname="$(_claude_tmux_session_name "$PWD" "$slot")"

  # 已有同名会话 -> 只 attach；否则新建会话运行 claude。
  # -t 目标带 = 前缀 = tmux 强制精确匹配。不带 = 时 tmux 找不到精确匹配会按
  # 前缀解析目标:slot1 名(pi-X)会误命中 slot2/3 会话(pi-X-2),致 pi 1/2/3
  # 打开同一会话。opencode/claude 包裹脚本同此修复。
  if tmux has-session -t "=$sname" 2>/dev/null; then
    tmux attach -t "=$sname"
  else
    # --- 约束：防止并行过多触发 OOM 断连 ---
    # 实例数 >= 上限、或有效可用内存(RAM available + swap free)低于阈值时拒绝启动。
    # 覆盖：  CLAUDE_FORCE=1 claude
    # 调优：  CLAUDE_MAX_INSTANCES（默认 6）、CLAUDE_MIN_HEADROOM_MB（默认 700）
    local cnt avail swapfree headroom
    cnt=$(pgrep -xc claude 2>/dev/null || echo 0)
    avail=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
    swapfree=$(awk '/^SwapFree:/{print $2}' /proc/meminfo)
    avail=${avail:-0}; swapfree=${swapfree:-0}
    headroom=$(( (avail + swapfree) / 1024 ))   # MB
    if [ "${CLAUDE_FORCE:-0}" != "1" ]; then
      if [ "${cnt:-0}" -ge "${CLAUDE_MAX_INSTANCES:-6}" ]; then
        printf 'claude: 已有 %s 个并行实例 (上限 %s)，为防 OOM 断连拒绝启动。\n' \
          "${cnt}" "${CLAUDE_MAX_INSTANCES:-6}" >&2
        printf '  确需启动: CLAUDE_FORCE=1 claude\n' >&2
        return 1
      fi
      if [ "${headroom}" -lt "${CLAUDE_MIN_HEADROOM_MB:-700}" ]; then
        printf 'claude: 可用内存仅 %sMB (RAM+swap，低于 %sMB)，启动可能 OOM 断连。\n' \
          "${headroom}" "${CLAUDE_MIN_HEADROOM_MB:-700}" >&2
        printf '  确需启动: CLAUDE_FORCE=1 claude\n' >&2
        return 1
      fi
    fi
    tmux new -s "$sname" -c "$PWD" "claude $*"
  fi
}
