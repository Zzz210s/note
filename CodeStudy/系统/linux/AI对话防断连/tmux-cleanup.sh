#!/usr/bin/env bash
# tmux-cleanup.sh
# 安装位置：~/claude-anti-drop/tmux-cleanup.sh（cron 运行，始终 exit 0）。
# 作用：回收「已 detach 且空闲超时」的 tmux 会话，释放被遗忘槽位占用的内存。
#       绝不杀 attached 或近期活跃的会话；只处理 cc-* 自动管理的会话。
# 环境变量覆盖：TMUX_BIN、THRESHOLD_HOURS / THRESHOLD_SEC、TMUX_CLEANUP_LOG、CONTINUUM_SAVE。

THRESHOLD_HOURS=24
threshold_sec="${THRESHOLD_SEC:-$((THRESHOLD_HOURS*3600))}"
TMUX_BIN="${TMUX_BIN:-tmux}"
LOG="${TMUX_CLEANUP_LOG:-$HOME/claude-anti-drop/tmux-cleanup.log}"
CONTINUUM_SAVE="${CONTINUUM_SAVE:-$HOME/.tmux/plugins/tmux-continuum/scripts/continuum_save.sh}"

# 纯判定：是否该杀这个会话？参数：name attached activity now threshold
# 返回 0=杀，1=跳过
_should_kill() {
  local name="$1" attached="$2" activity="$3" now="$4" thr="$5"
  case "$name" in cc-*) ;; *) return 1 ;; esac       # 只处理受管理的会话
  [ "$attached" = "0" ] || return 1                   # 只处理已 detach 的
  (( now - activity > thr )) || return 1              # 只处理空闲超时的
  return 0
}

_main() {
  local now killed=0
  now=$(date +%s)
  mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

  local name attached activity
  while IFS='|' read -r name attached activity; do
    [ -n "$name" ] || continue
    if _should_kill "$name" "$attached" "$activity" "$now" "$threshold_sec"; then
      if $TMUX_BIN kill-session -t "$name" 2>/dev/null; then
        killed=$((killed+1))
        printf '%s | killed %s | idle %sh\n' "$(date '+%F %T %Z')" "$name" \
          "$((( now - activity ) / 3600 ))" >> "$LOG"
      fi
    fi
  done < <($TMUX_BIN list-sessions -F '#{session_name}|#{session_attached}|#{session_activity}' 2>/dev/null)

  if [ "$killed" -gt 0 ] && [ -n "$CONTINUUM_SAVE" ] && [ -x "$CONTINUUM_SAVE" ]; then
    # best-effort：杀完强制保存一次，避免被杀会话在重启后被恢复。
    $TMUX_BIN run-shell "$CONTINUUM_SAVE" 2>/dev/null || true
  fi

  printf '%s | ran | killed=%s\n' "$(date '+%F %T %Z')" "$killed" >> "$LOG"
  exit 0
}

if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then _main "$@"; fi
