#!/bin/bash
# sync-personas-store.sh — 同步本地 personas/ 到 clawdBoxStore GitHub 仓库
# 用法: ./scripts/sync-personas-store.sh
# 依赖: git remote "store" 已配置（含 PAT 认证）

set -euo pipefail

L="$(cd "$(dirname "$0")/.." && pwd)"
STORE_DIR="/tmp/clawdboxstore-sync"
STORE_URL=$(git -C "$L" remote get-url store 2>/dev/null || echo "")

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
die()  { echo -e "${RED}✗${NC} $*"; exit 1; }

[ -z "$STORE_URL" ] && die "remote 'store' 未配置，先运行: git remote add store https://<PAT>@github.com/wzydxb/clawdBoxStore.git"

echo "同步 personas → clawdBoxStore..."

# 克隆 store（浅克隆，只取最新）
rm -rf "$STORE_DIR"
git clone --depth=1 "$STORE_URL" "$STORE_DIR" 2>/dev/null
ok "clawdBoxStore 已拉取"

# 覆盖 personas 目录（保留 store 里有但本地没有的文件）
# 策略：本地 personas/ 为主，只推送本地存在的文件，不删除 store 里多余的文件
rsync -av --exclude="manifest.json" --exclude="README.md" \
  --exclude="__pycache__/" --exclude="*.pyc" --exclude="*.pyo" \
  "$L/personas/" "$STORE_DIR/personas/" 2>/dev/null
ok "personas 文件已同步"

# 提交推送
cd "$STORE_DIR"
git add personas/
if git diff --cached --quiet; then
  ok "无变更，personas 已是最新"
  rm -rf "$STORE_DIR"
  exit 0
fi

CHANGED=$(git diff --cached --name-only | wc -l | tr -d ' ')
git commit -m "sync personas from hermes-opc (${CHANGED} files changed)"
git push origin main
ok "已推送到 clawdBoxStore/personas（${CHANGED} 个文件）"

rm -rf "$STORE_DIR"
echo ""
echo "Done. 查看: https://github.com/wzydxb/clawdBoxStore/tree/main/personas"
