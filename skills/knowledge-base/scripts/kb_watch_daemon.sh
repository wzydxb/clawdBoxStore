#!/bin/bash
# kb_watch_daemon.sh — inotifywait 守护进程（由 kb-watcher.service 启动）
#
# 两个监听循环并行运行：
#   inbox watcher：只监听 $MOUNT/inbox/，新文件触发整理归类 + 推送通知
#   main watcher ：监听整个 $MOUNT/（排除 inbox 和 .hermes-index），静默更新索引

set -euo pipefail

H="${HERMES_HOME:-/root/.hermes}"
SCRIPTS="$H/skills/knowledge-base/scripts"

MOUNT=$(python3 -c "
import re
c = open('$H/USER.md').read()
m = re.search(r'挂载路径:\s*(.+)', c)
print(m.group(1).strip() if m else '/userdata/uploads')
" 2>/dev/null || echo "/userdata/uploads")

INBOX="$MOUNT/inbox"
mkdir -p "$MOUNT" "$INBOX"
echo "[$(date '+%H:%M:%S')] kb_watch_daemon 启动，MOUNT=$MOUNT" >&2

INBOX_SILENCE_SEC=30   # inbox：最后一个文件到达后静默30秒才触发
MAIN_DEBOUNCE_SEC=8    # main：普通前沿防抖
INBOX_PENDING="/tmp/kb_inbox_pending"
INBOX_FILES="/tmp/kb_inbox_files"

# ── inbox watcher：只标记，不直接触发 ───────────────────────
inbox_watcher() {
  inotifywait -m -r -e close_write,moved_to,create --format '%f' "$INBOX" \
    2>/dev/null | \
  while IFS= read -r FNAME; do
    case "$FNAME" in
      .DS_Store|._*|.Spotlight*|.Trashes*|*.tmp|~\$*) continue ;;
    esac
    echo "[$(date '+%H:%M:%S')] [inbox] 收到文件: $FNAME" >&2
    echo "$FNAME" >> "$INBOX_FILES"
    touch "$INBOX_PENDING"   # 每来一个文件都刷新 mtime
  done
}

# ── inbox timer：尾沿触发，沉默 INBOX_SILENCE_SEC 秒后触发一次 ──
inbox_timer() {
  while true; do
    sleep 5
    [ -f "$INBOX_PENDING" ] || continue
    MTIME=$(stat -c %Y "$INBOX_PENDING" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    (( NOW - MTIME < INBOX_SILENCE_SEC )) && continue

    # 沉默够久，触发
    rm -f "$INBOX_PENDING"
    FLIST=$(cat "$INBOX_FILES" 2>/dev/null | sort -u | tr '\n' ' ')
    rm -f "$INBOX_FILES"
    echo "[$(date '+%H:%M:%S')] [inbox] 静默结束，触发处理: $FLIST" >&2
    bash "$SCRIPTS/kb_watcher.sh" "$INBOX" "$FLIST" --mode inbox 2>>/tmp/kb_watcher.log
  done
}

# ── main watcher：静默更新索引 ───────────────────────────────
main_watcher() {
  local LAST_RUN=0
  inotifywait -m -r -e close_write,moved_to,moved_from,create,delete --format '%e %f' "$MOUNT" \
    --exclude '(\.hermes-index|/inbox/)' 2>/dev/null | \
  while IFS=' ' read -r EVENT FNAME; do
    case "$FNAME" in
      .DS_Store|._*|.Spotlight*|.Trashes*|*.tmp|~\$*) continue ;;
    esac

    NOW=$(date +%s)
    if (( NOW - LAST_RUN < MAIN_DEBOUNCE_SEC )); then
      continue
    fi
    LAST_RUN=$NOW

    echo "[$(date '+%H:%M:%S')] [main] $EVENT: $FNAME" >&2
    bash "$SCRIPTS/kb_watcher.sh" "$MOUNT" "$FNAME" --mode main 2>>/tmp/kb_watcher.log
  done
}

inbox_watcher &
inbox_timer &
main_watcher &
wait
