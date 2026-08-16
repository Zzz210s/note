# pi auto-tmux protection
# 安装位置：~/.pi-tmux.sh，由 ~/.bashrc 末尾 source。
# 作用：让交互式 `pi` 跑在「每项目一个」的持久 tmux 会话里，
#       使其在 SSH 掉线 / VS Code 关闭后依然存活。
# 重连：在同一项目目录再敲 `pi`，或 `tmux a -t <session>`。
# 停用：注释掉 ~/.bashrc 里的 source 行。

# 按项目目录推导会话名：pi-<目录名>-<cksum4>
_pi_tmux_session_name() {
  local pwd="${1:-$PWD}"
  local name="pi-$(basename "${pwd:-/}")-$(printf '%s' "$pwd" | cksum | cut -c1-4)"
  name="${name//[^A-Za-z0-9_-]/_}"
  printf '%s' "$name"
}

pi() {
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
  sname="$(_pi_tmux_session_name "$PWD")"

  # 已有同名会话 -> 只 attach（不会重复运行 pi，避免二次启动）；
  # 否则新建会话并在 $PWD 运行 pi。
  if tmux has-session -t "$sname" 2>/dev/null; then
    tmux attach -t "$sname"
  else
    tmux new -s "$sname" -c "$PWD" "pi $*"
  fi
}
