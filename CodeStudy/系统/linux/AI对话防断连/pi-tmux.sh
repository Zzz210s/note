# pi auto-tmux protection
# 安装位置：~/.pi-tmux.sh，由 ~/.bashrc 末尾 source。
# 作用：让交互式 `pi` 跑在「每项目一个」的持久 tmux 会话里，
#       使其在 SSH 掉线 / VS Code 关闭后依然存活。
# 重连：在同一项目目录再敲 `pi`，或 `tmux a -t <session>`。
# 停用：注释掉 ~/.bashrc 里的 source 行。

# 按项目目录推导会话名：pi-<目录名>-<cksum4>
_pi_tmux_session_name() {
  local pwd="${1:-$PWD}" slot="${2:-1}"
  (( slot < 1 )) && slot=1
  local name="pi-$(basename "${pwd:-/}")-$(printf '%s' "$pwd" | cksum | cut -c1-4)"
  name="${name//[^A-Za-z0-9_-]/_}"
  (( slot > 1 )) && name="${name}-${slot}"
  printf '%s' "$name"
}

pi() {
  # 可选数字槽位：`pi 2`、`pi 3` ... -> 同目录不同会话。
  local slot=1
  if [[ ${1:-} =~ ^[0-9]+$ ]]; then
    slot=$1; shift
    (( slot < 1 )) && slot=1
  fi

  # 只保护交互式入口；其余参数（-p/--print、export、install/update/config/auth 等）原样透传，
  # 不影响脚本化调用。
  case "${1:-}" in
    ""|-c|--continue|-r|--resume)
      ;;
    *)
      command pi "$@"
      return $?
      ;;
  esac

  # 已在 tmux 内 -> 直接运行，不嵌套。
  if [ -n "$TMUX" ]; then
    command pi "$@"
    return $?
  fi

  # 未装 tmux -> 回退为裸 pi。
  if ! command -v tmux >/dev/null 2>&1; then
    command pi "$@"
    return $?
  fi

  local sname
  sname="$(_pi_tmux_session_name "$PWD" "$slot")"

  # 已有同名会话 -> 只 attach（不会重复运行 pi，避免二次启动）；
  # 否则新建会话并在 $PWD 运行 pi。
  if tmux has-session -t "$sname" 2>/dev/null; then
    tmux attach -t "$sname"
  else
    # --- 约束：防止并行过多触发 OOM 断连 ---
    # 实例数 >= 上限时拒绝启动。覆盖：PI_FORCE=1 pi；调优：PI_MAX_INSTANCES（默认 6）
    local cnt
    cnt=$(pgrep -xc pi 2>/dev/null || echo 0)
    if [ "${PI_FORCE:-0}" != "1" ] && [ "${cnt:-0}" -ge "${PI_MAX_INSTANCES:-6}" ]; then
      printf 'pi: 已有 %s 个并行实例 (上限 %s)，为防 OOM 断连拒绝启动。\n' \
        "${cnt}" "${PI_MAX_INSTANCES:-6}" >&2
      printf '  确需启动: PI_FORCE=1 pi\n' >&2
      return 1
    fi
    tmux new -s "$sname" -c "$PWD" "pi $*"
  fi
}
