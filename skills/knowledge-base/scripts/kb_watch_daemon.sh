#!/bin/bash
# kb_watch_daemon.sh — inotifywait 守护进程（由 kb-watcher.service 启动）
# 监听文件变化，触发 kb_watcher.sh + hermes cron run
# 内置防抖（8秒）和 Mac 元数据文件过滤

set -euo pipefail

H="${HERMES_HOME:-/root/.hermes}"
SCRIPTS="$H/skills/knowledge-base/scripts"

# 从 USER.md 解析挂载路径
MOUNT=$(python3 -c "
import re
c = open('$H/USER.md').read()
m = re.search(r'挂载路径:\s*(.+)', c)
print(m.group(1).strip() if m else '/userdata/uploads')
" 2>/dev/null || echo "/userdata/uploads")

mkdir -p "$MOUNT"
echo "[$(date '+%H:%M:%S')] kb_watch_daemon 启动，监听 $MOUNT" >&2

DEBOUNCE_SEC=8
LAST_RUN=0

inotifywait -m -r -e close_write,moved_to,create --format '%f' "$MOUNT" \
  --exclude '.hermes-index' 2>/dev/null | \
while IFS= read -r FNAME; do
  # 过滤 Mac SMB 元数据文件
  case "$FNAME" in
    .DS_Store|._*|.Spotlight*|.Trashes*|*.tmp|~\$*) continue ;;
  esac

  # 防抖：8秒内同一批变化只触发一次
  NOW=$(date +%s)
  DIFF=$(( NOW - LAST_RUN ))
  if [ "$DIFF" -lt "$DEBOUNCE_SEC" ]; then
    echo "[$(date '+%H:%M:%S')] 防抖跳过: $FNAME" >&2
    continue
  fi
  LAST_RUN=$NOW

  echo "[$(date '+%H:%M:%S')] 检测到变化: $FNAME" >&2
  bash "$SCRIPTS/kb_watcher.sh" "$MOUNT" "$FNAME" 2>>/tmp/kb_watcher.log
done
