# opencode anti-drop wrapper
# 安装位置：~/.opencode-tmux.sh，由 ~/.bashrc 末尾 source。
# 作用：包裹交互式 `opencode`，让它跑在「每项目一个」的持久 tmux 会话里；
#       并在 opencode 退出后（包括误按 Ctrl+C 退出 TUI）落到一个小提示，
#       回车即 `opencode --continue` 续上上次会话。
#       opencode 每条消息都会写入 SQLite，其实不会丢；这里只是让恢复一键完成。
# 停用：注释掉 ~/.bashrc 里的 source 行。
# 单次绕过：`command opencode …` 或 `opencode --plain …`。

# 按项目目录推导会话名：oc-<目录名>-<cksum4>
_opencode_tmux_session_name() {
  local pwd="${1:-$PWD}" slot="${2:-1}"
  (( slot < 1 )) && slot=1
  local name="oc-$(basename "${pwd:-/}")-$(printf '%s' "$pwd" | cksum | cut -c1-4)"
  name="${name//[^A-Za-z0-9_-]/_}"
  (( slot > 1 )) && name="${name}-${slot}"
  printf '%s' "$name"
}

opencode() {
  # 可选数字槽位：`opencode 2`、`opencode 3` ... -> 同目录不同会话。
  local slot=1
  if [[ ${1:-} =~ ^[0-9]+$ ]]; then
    slot=$1; shift
    (( slot < 1 )) && slot=1
  fi

  # 子命令必须原样透传（它们打印后退出，包裹成续会话循环会死循环或吞输出）。
  case "${1:-}" in
    completion|acp|mcp|attach|run|debug|providers|auth|agent|upgrade|uninstall|\
serve|web|models|stats|export|import|github|pr|session|plugin|plug|db)
      command opencode "$@"; return $? ;;
  esac

  # 显式退出包裹（开一个全新的裸 opencode）。
  if [ "${1:-}" = "--plain" ]; then
    shift
    command opencode "$@"
    return $?
  fi

  # 未装 tmux -> 退化为当前 shell 内的续会话循环，至少保留「回车即续」。
  if [ -z "$TMUX" ] && ! command -v tmux >/dev/null 2>&1; then
    while :; do
      command opencode --continue "$@"
      echo
      echo "── opencode 已退出（可能是 Ctrl+C / EOF）。会话历史已自动保存 ──"
      local ans
      read -r -p "Enter=--continue 接上次会话  |  n=开新会话  |  q=退出 shell: " ans
      case "$ans" in q) break ;; n) command opencode ;; esac
    done
    return $?
  fi

  # 已在 tmux 内 -> 直接跑 opencode，退出后给续会话提示。
  if [ -n "$TMUX" ]; then
    while :; do
      command opencode --continue "$@"
      echo
      echo "── opencode 已退出（可能是 Ctrl+C / EOF）。会话历史已自动保存 ──"
      local ans
      read -r -p "Enter=--continue 接上次会话  |  n=开新会话  |  q=留在 shell: " ans
      case "$ans" in q) break ;; n) command opencode ;; esac
    done
    return $?
  fi

  # tmux 之外且 tmux 可用 -> 包进每目录一个的 tmux 会话，自动续上次会话。
  local sname
  sname="$(_opencode_tmux_session_name "$PWD" "$slot")"

  # -t 目标带 = 前缀 = tmux 强制精确匹配。不带 = 时 tmux 找不到精确匹配会按
  # 前缀解析目标:slot1 名(pi-X)会误命中 slot2/3 会话(pi-X-2),致 pi 1/2/3
  # 打开同一会话。opencode/claude 包裹脚本同此修复。
  if tmux has-session -t "=$sname" 2>/dev/null; then
    tmux attach -t "=$sname"
  else
    # --- 约束：防止并行过多触发 OOM 断连 ---
    # 实例数 >= 上限时拒绝启动。覆盖：OPENCODE_FORCE=1 opencode；调优：OPENCODE_MAX_INSTANCES（默认 6）
    local cnt
    cnt=$(pgrep -xc opencode 2>/dev/null || echo 0)
    if [ "${OPENCODE_FORCE:-0}" != "1" ] && [ "${cnt:-0}" -ge "${OPENCODE_MAX_INSTANCES:-6}" ]; then
      printf 'opencode: 已有 %s 个并行实例 (上限 %s)，为防 OOM 断连拒绝启动。\n' \
        "${cnt}" "${OPENCODE_MAX_INSTANCES:-6}" >&2
      printf '  确需启动: OPENCODE_FORCE=1 opencode\n' >&2
      return 1
    fi
    # 内部命令在退出后回车即 `opencode --continue` 续会话；
    # `n` 跑全新裸 opencode；`q` 退出并结束 tmux 会话。
    tmux new -s "$sname" -c "$PWD" '
      while :; do
        command opencode --continue '"$*"'
        echo
        echo "── opencode 已退出（可能是 Ctrl+C / EOF）。会话历史已自动保存 ──"
        read -r -p "Enter=--continue 接上次会话  |  n=开新会话  |  q=退出 tmux: " _a
        case "$_a" in q) break ;; n) command opencode ;; esac
      done
    '
  fi
}
