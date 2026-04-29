#!/bin/bash
# kb_watcher.sh — 文件变化触发器
# 用法: kb_watcher.sh <mount_path> <changed_file> [--mode inbox|main]
#
# --mode inbox: 新文件进 inbox，触发整理归类 + 推送通知（默认）
# --mode main : 主目录变化，只静默更新索引和实体图谱，不推送

set -euo pipefail

MOUNT="${1:-/userdata/uploads}"
CHANGED_FILE="${2:-}"
MODE="${4:-inbox}"

H="${HERMES_HOME:-/root/.hermes}"
SCRIPTS="$H/skills/knowledge-base/scripts"
PENDING_SUMMARY="/tmp/kb_pending_summary"
LOCK="/tmp/kb_watcher.lock"

# 防并发
exec 9>"$LOCK"
flock -n 9 || exit 0

log() { echo "[$(date '+%H:%M:%S')] [$MODE] $*" >&2; }

# 1. 增量索引
log "增量扫描 $MOUNT ..."
INDEX_OUT=$(python3 "$SCRIPTS/kb_index.py" "$MOUNT" 2>/dev/null || echo "")
NEW_COUNT=$(echo "$INDEX_OUT" | grep -oP '新增 \K\d+' || echo "0")
UPD_COUNT=$(echo "$INDEX_OUT" | grep -oP '更新 \K\d+' || echo "0")

if [ "$NEW_COUNT" = "0" ] && [ "$UPD_COUNT" = "0" ]; then
  log "无变化，退出"
  exit 0
fi

log "新增 $NEW_COUNT，更新 $UPD_COUNT"

# 2. 更新 entities.json
log "更新实体图谱 ..."
if [ -n "$CHANGED_FILE" ]; then
  python3 "$SCRIPTS/kb_entities.py" "$MOUNT" --update "$CHANGED_FILE" 2>/dev/null || true
else
  python3 "$SCRIPTS/kb_entities.py" "$MOUNT" --list 2>/dev/null | python3 - << 'PYEOF' 2>/dev/null || true
import sys, json, os, re
from datetime import date

lines = sys.stdin.read()
files = re.findall(r'文件：(.+\.(?:docx|xlsx|pdf))', lines)
mount = os.environ.get('MOUNT', '/userdata/uploads')
entities_path = os.path.join(mount, '.hermes-index', 'entities.json')

try:
    data = json.load(open(entities_path))
except:
    data = {"updated": "", "entities": {}, "relations": []}

today = date.today().isoformat()
for f in files:
    name = os.path.basename(f)
    for school in ['中南大学', '湖南大学', '湖南师范大学', '中南林业科技大学']:
        if school in name:
            if school not in data['entities']:
                data['entities'][school] = {"files": [], "type": "组织", "last_seen": today}
            if name not in data['entities'][school]['files']:
                data['entities'][school]['files'].append(name)
                data['entities'][school]['last_seen'] = today

data['updated'] = today + 'T' + __import__('datetime').datetime.now().strftime('%H:%M:%S')
json.dump(data, open(entities_path, 'w'), ensure_ascii=False, indent=2)
PYEOF
fi

# 3. 刷新 SOUL.md 静态实体块
log "刷新 SOUL.md 实体块 ..."
ENTITIES_OUT=$(python3 "$SCRIPTS/kb_entities.py" "$MOUNT" --read 2>/dev/null || echo "")
if [ -n "$ENTITIES_OUT" ]; then
  python3 << PYEOF
import re
content = open('$H/SOUL.md').read()
entities = """$ENTITIES_OUT"""
block = f"""
<!-- KB_ENTITIES_START -->
### 本地知识库实体索引（静态注入，随文件更新自动刷新）

以下词语出现在用户问题中时，**必须优先调用 \`skill_view("knowledge-base/kb-search")\` 检索本地文件，禁止直接调用 opencli 搜索引擎**：

{entities}
<!-- KB_ENTITIES_END -->
"""
content = re.sub(r'\n<!-- KB_ENTITIES_START -->.*?<!-- KB_ENTITIES_END -->\n', block, content, flags=re.DOTALL)
open('$H/SOUL.md', 'w').write(content)
print('SOUL.md updated')
PYEOF
fi

# 4. inbox 模式：写 pending summary + 触发推送
if [ "$MODE" = "inbox" ]; then
  log "写入 pending summary ..."
  {
    echo "=== $(date '+%Y-%m-%d %H:%M') ==="
    echo "新增: $NEW_COUNT 个文件，更新: $UPD_COUNT 个文件"
    if [ -n "$CHANGED_FILE" ]; then
      echo "文件: $(basename "$CHANGED_FILE")"
    fi
    LOG_MD="$MOUNT/.hermes-index/wiki/log.md"
    [ -f "$LOG_MD" ] && tail -3 "$LOG_MD"
  } >> "$PENDING_SUMMARY"

  KB_NOTIFY_JOB_ID="963573a5e84d"
  log "触发 hermes cron run $KB_NOTIFY_JOB_ID ..."
  hermes cron run "$KB_NOTIFY_JOB_ID" 2>>/tmp/kb_watcher.log || true
else
  log "main 模式，索引已更新，不推送"
fi

log "完成"
