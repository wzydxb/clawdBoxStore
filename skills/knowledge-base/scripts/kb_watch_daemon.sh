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

DEBOUNCE_SEC=8

# ── inbox watcher：触发整理 + 推送 ──────────────────────────
inbox_watcher() {
  local LAST_RUN=0
  inotifywait -m -r -e close_write,moved_to,create --format '%f' "$INBOX" \
    2>/dev/null | \
  while IFS= read -r FNAME; do
    case "$FNAME" in
      .DS_Store|._*|.Spotlight*|.Trashes*|*.tmp|~\$*) continue ;;
    esac

    NOW=$(date +%s)
    if (( NOW - LAST_RUN < DEBOUNCE_SEC )); then
      echo "[$(date '+%H:%M:%S')] [inbox] 防抖跳过: $FNAME" >&2
      continue
    fi
    LAST_RUN=$NOW

    echo "[$(date '+%H:%M:%S')] [inbox] 新文件: $FNAME" >&2
    bash "$SCRIPTS/kb_watcher.sh" "$INBOX" "$FNAME" --mode inbox 2>>/tmp/kb_watcher.log
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
    if (( NOW - LAST_RUN < DEBOUNCE_SEC )); then
      continue
    fi
    LAST_RUN=$NOW

    echo "[$(date '+%H:%M:%S')] [main] $EVENT: $FNAME" >&2
    bash "$SCRIPTS/kb_watcher.sh" "$MOUNT" "$FNAME" --mode main 2>>/tmp/kb_watcher.log
  done
}

inbox_watcher &
main_watcher &
wait
