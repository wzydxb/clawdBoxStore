#!/bin/bash
# env-init.sh — 运行环境一键初始化
# 用法: bash scripts/env-init.sh
# 支持: Debian 12 / Ubuntu 22.04+ · ARM (aarch64) / Intel (x86_64)
# 必须以 root 身份运行

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
die()  { echo -e "${RED}✗${NC} $*"; exit 1; }
step() { echo -e "\n${YELLOW}[$1]${NC} $2"; }

# root 检查
[ "$EUID" -eq 0 ] || die "请以 root 身份运行: sudo bash $0"

# 脚本所在目录（兼容 symlink 和 source）
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
REPO_DIR="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"

# HOME 保底（sudo 环境可能未设置）
HOME="${HOME:-/root}"

# ── 1. Python ─────────────────────────────────────────────
step "1/4" "Python 运行时"

# hermes venv 是 agent 实际运行环境，优先用它；系统 python3 作为工具（装包用）
HERMES_VENV="${HOME}/.hermes/hermes-agent/venv"
HERMES_PY="${HERMES_VENV}/bin/python3"

if [ ! -x "$HERMES_PY" ]; then
  die "hermes venv 不存在：$HERMES_PY\n请先安装 hermes agent"
fi

# 系统 python3 必须存在（用于 pip install --target）
if ! command -v python3 &>/dev/null; then
  warn "系统 python3 未安装，正在安装..."
  apt-get update -qq && apt-get install -y python3 python3-pip || die "python3 安装失败"
fi
if ! python3 -m pip --version &>/dev/null; then
  apt-get install -y python3-pip 2>/dev/null || true
fi

ok "hermes venv: $($HERMES_PY --version)"

# venv 标准库检查
"$HERMES_PY" -c "import json,argparse,sys,statistics,math,datetime" \
  || die "venv 标准库检查失败"

# venv 里装 playwright（canvas 渲染依赖）
if ! "$HERMES_PY" -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
  warn "hermes venv 缺少 playwright，正在安装..."
  SITE=$("$HERMES_PY" -c "import site; print(site.getsitepackages()[0])")
  python3 -m pip install --target="$SITE" playwright -q 2>/dev/null \
    && ok "playwright 已安装到 hermes venv" \
    || warn "playwright 安装失败，canvas 渲染可能不可用"
else
  ok "playwright 已就绪（hermes venv）"
fi

# 用 venv python3 验证所有 persona 脚本语法
FAIL=0
while IFS= read -r f; do
  "$HERMES_PY" -m py_compile "$f" 2>/dev/null || { warn "语法错误: $f"; FAIL=1; }
done < <(find "$REPO_DIR/personas" -name "*.py" 2>/dev/null)
[ "$FAIL" -eq 0 ] && ok "persona 脚本语法全部通过" || warn "部分脚本有语法错误，请检查"

# ── 2. opencli ────────────────────────────────────────────
step "2/4" "opencli 工具链"

if ! command -v opencli &>/dev/null; then
  warn "opencli 未安装，正在安装..."
  if command -v bun &>/dev/null; then
    bun add -g @jackwener/opencli || die "bun 安装 opencli 失败"
  elif command -v npm &>/dev/null; then
    npm install -g @jackwener/opencli || die "npm 安装 opencli 失败"
  else
    die "需要 npm 或 bun 来安装 opencli，请先安装 Node.js:\n  apt-get install -y nodejs npm"
  fi
fi

ok "opencli $(opencli --version 2>/dev/null || echo '已安装')"

# opencli extension 连接检查（仅在 VNC/X11 环境下尝试修复）
DOCTOR_OUT="$(opencli doctor 2>/dev/null || true)"
if echo "$DOCTOR_OUT" | grep -q "Extension: connected"; then
  ok "opencli extension 已连接"
elif xdpyinfo -display :1 &>/dev/null 2>&1; then
  # VNC display :1 存在，尝试重启 Chromium
  warn "opencli extension 未连接，尝试重启 Chromium..."
  pkill -f '/usr/bin/chromium' 2>/dev/null || true
  sleep 2
  AUTOSTART="/root/.config/autostart/chromium.desktop"
  if [ -f "$AUTOSTART" ]; then
    EXEC_LINE="$(grep '^Exec=' "$AUTOSTART" | sed 's/^Exec=//')"
    DISPLAY=:1 XAUTHORITY=/root/.Xauthority setsid $EXEC_LINE &>/dev/null &
    sleep 5
    if opencli doctor 2>/dev/null | grep -q "Extension: connected"; then
      ok "opencli extension 已重连"
    else
      warn "extension 仍未连接，请在 VNC 中手动检查 Chromium"
    fi
  else
    warn "找不到 autostart 配置，请手动启动 Chromium 并确保包含 --remote-debugging-port=9222"
  fi
else
  warn "VNC display :1 不可用，Chromium 将在首次使用浏览器时自动启动"
fi

# ── 3. 搜索适配器 ─────────────────────────────────────────
step "3/4" "搜索适配器"

ADAPTERS_DIR="${HOME}/.opencli/clis"
NEED_COPY=0

for site in baidu bing so sogou sohu; do
  [ ! -f "$ADAPTERS_DIR/$site/search.js" ] && NEED_COPY=1 && break
done

if [ "$NEED_COPY" -eq 1 ]; then
  warn "搜索适配器缺失，正在部署..."
  for site in baidu bing so sogou sohu; do
    mkdir -p "$ADAPTERS_DIR/$site" || die "无法创建目录: $ADAPTERS_DIR/$site"
    SRC="$REPO_DIR/opencli-adapters/$site/search.js"
    if [ -f "$SRC" ]; then
      cp "$SRC" "$ADAPTERS_DIR/$site/search.js"
      ok "  $site/search.js"
    else
      warn "  源文件不存在: $SRC"
    fi
  done
else
  ok "搜索适配器已就绪（baidu / bing / so / sogou / sohu）"
fi

# ── 4. 网盘（Samba）─────────────────────────────────────
step "4/4" "网盘挂载"

HAS_SYSTEMCTL=0
command -v systemctl &>/dev/null && HAS_SYSTEMCTL=1

SAMBA_ACTIVE=0
if [ "$HAS_SYSTEMCTL" -eq 1 ] && systemctl is-active smbd &>/dev/null; then
  SAMBA_ACTIVE=1
fi

if [ "$SAMBA_ACTIVE" -eq 1 ]; then
  ok "Samba 服务运行中"
else
  warn "Samba 未运行"
  if command -v smbd &>/dev/null; then
    warn "尝试启动 smbd / nmbd..."
    if [ "$HAS_SYSTEMCTL" -eq 1 ]; then
      systemctl start smbd nmbd && ok "Samba 已启动" || warn "启动失败，请手动检查: systemctl status smbd"
    else
      smbd -D && nmbd -D && ok "Samba 已启动（非 systemd）" || warn "启动失败"
    fi
  else
    warn "Samba 未安装。如需网盘功能，请运行 skill_view(\"system-setup/network-drive\") 完成部署"
  fi
fi

# workspace 软链
if [ -L "/root/workspace/uploads" ]; then
  ok "workspace 软链: /root/workspace/uploads → $(readlink -f /root/workspace/uploads)"
elif [ -d "/data/uploads" ]; then
  warn "软链缺失，正在创建..."
  mkdir -p /root/workspace
  ln -sfn /data/uploads /root/workspace/uploads
  ok "workspace 软链已创建"
else
  warn "/data/uploads 不存在，网盘未部署（非必须，可跳过）"
fi

# ── 完成 ──────────────────────────────────────────────────
SAMBA_STATUS="inactive"
if [ "$HAS_SYSTEMCTL" -eq 1 ]; then
  SAMBA_STATUS="$(systemctl is-active smbd 2>/dev/null || true)"
  [ -z "$SAMBA_STATUS" ] && SAMBA_STATUS="inactive"
fi

ADAPTERS_LIST="$(ls -d "$ADAPTERS_DIR"/* 2>/dev/null | xargs -I{} basename {} | tr '\n' ' ' || echo 'none')"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  环境初始化完成${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  架构    : $(uname -m)"
echo "  Python  : $($HERMES_PY --version) (hermes venv)"
echo "  opencli : $(opencli --version 2>/dev/null || echo '已安装')"
echo "  适配器  : ${ADAPTERS_LIST}"
echo "  Samba   : ${SAMBA_STATUS}"
echo ""
