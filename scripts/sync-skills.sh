#!/bin/bash
# sync-skills.sh — 快速同步 Skills 到服务器（不覆盖 USER.md）
# 用法: ./scripts/sync-skills.sh root@192.168.10.76

TARGET="${1:-root@192.168.10.76}"
H="/root/.hermes"
L="$(cd "$(dirname "$0")/.." && pwd)"

echo "同步 Skills 到 $TARGET..."

# 核心配置
scp "$L/SOUL.md" "$TARGET:$H/SOUL.md"
scp "$L/AGENTS.md" "$TARGET:$H/AGENTS.md"
echo "✓ SOUL.md + AGENTS.md"

# 基础技能
ssh "$TARGET" "mkdir -p $H/skills/reporting $H/skills/retrospective"
scp "$L/skills/base/reporting/SKILL.md" "$TARGET:$H/skills/reporting/SKILL.md"
scp "$L/skills/base/retrospective/SKILL.md" "$TARGET:$H/skills/retrospective/SKILL.md"
echo "✓ Base skills"

# 批量上传角色技能
for role_dir in pm:product-manager finance:finance-manager hr:hr-manager ops:operations-manager ceo:ceo; do
  ns="${role_dir%%:*}"
  local_role="${role_dir##*:}"
  count=0
  while IFS= read -r f; do
    rel="${f#$L/skills/roles/$local_role/}"
    dir="$(dirname "$rel")"
    ssh "$TARGET" "mkdir -p $H/skills/$ns/$dir" 2>/dev/null
    scp "$f" "$TARGET:$H/skills/$ns/$rel" 2>/dev/null && count=$((count+1))
  done < <(find "$L/skills/roles/$local_role" -name 'SKILL.md')
  echo "✓ $ns: $count SKILL.md files"
done

echo ""
echo "验证:"
ssh "$TARGET" "find $H/skills -name 'SKILL.md' | wc -l | xargs echo 'Total SKILL.md:'"
echo "Done!"
