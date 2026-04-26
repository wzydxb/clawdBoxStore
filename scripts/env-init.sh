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
step "1/5" "Python 运行时"

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

# ── 2. 浏览器工具链 ───────────────────────────────────────
step "2/5" "浏览器工具链（agent-browser + CDP）"

# playwright headless_shell（hermes browser toolset 依赖）
HEADLESS_OK=$("$HERMES_PY" -c "
import subprocess, sys
r = subprocess.run(['python3', '-m', 'playwright', 'install', '--dry-run', 'chromium'],
    capture_output=True, text=True)
# 检查 headless_shell 是否已下载
import pathlib, glob
shells = glob.glob(str(pathlib.Path.home()) + '/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell')
print('OK' if shells else 'MISSING')
" 2>/dev/null || echo "MISSING")

if [ "$HEADLESS_OK" != "OK" ]; then
  warn "playwright headless_shell 未安装，正在下载..."
  "$HERMES_PY" -m playwright install chromium 2>&1 | tail -2 \
    && ok "playwright headless_shell 已安装" \
    || warn "headless_shell 安装失败（ARM 架构将回退 CDP 模式）"
else
  ok "playwright headless_shell 已就绪"
fi

# agent-browser（hermes browser toolset 的 CLI 驱动）
NVM_SH="${HOME}/.nvm/nvm.sh"
_npm() { [ -f "$NVM_SH" ] && source "$NVM_SH" 2>/dev/null; npm "$@"; }
_npx() { [ -f "$NVM_SH" ] && source "$NVM_SH" 2>/dev/null; npx "$@"; }

if ! _npx agent-browser --version &>/dev/null 2>&1; then
  warn "agent-browser 未安装，正在安装..."
  _npm install -g agent-browser -q 2>&1 | tail -2 \
    && ok "agent-browser 已安装" \
    || warn "agent-browser 安装失败"
else
  ok "agent-browser 已就绪"
fi

# ARM64 上 agent-browser 无法下载 Chrome for Testing，改用 CDP 连接已有 Chromium
ARCH="$(uname -m)"
if [ "$ARCH" = "aarch64" ]; then
  # 确认 9222 端口有 Chromium 在监听
  CDP_OK=$(curl -s --max-time 3 http://localhost:9222/json/version 2>/dev/null | grep -c '"Browser"' || true)
  if [ "$CDP_OK" -gt 0 ]; then
    # 注入 BROWSER_CDP_URL 到 hermes gateway service
    SVC="${HOME}/.config/systemd/user/hermes-gateway.service"
    if [ -f "$SVC" ] && ! grep -q "BROWSER_CDP_URL" "$SVC"; then
      sed -i '/^\[Service\]/a Environment=BROWSER_CDP_URL=http://localhost:9222' "$SVC"
      systemctl --user daemon-reload 2>/dev/null || true
      systemctl --user restart hermes-gateway.service 2>/dev/null || true
      ok "ARM64 CDP 模式：BROWSER_CDP_URL 已注入 gateway service"
    else
      ok "ARM64 CDP 模式：BROWSER_CDP_URL 已配置"
    fi
    # 写入 /etc/environment 兜底
    grep -q "BROWSER_CDP_URL" /etc/environment 2>/dev/null \
      || echo "BROWSER_CDP_URL=http://localhost:9222" >> /etc/environment
  else
    warn "ARM64：9222 端口无 Chromium，浏览器工具将在首次使用时尝试启动"
  fi
fi

# ── 3. opencli ────────────────────────────────────────────
step "3/5" "opencli 工具链"

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

# ── 真实浏览器检查与修复 ──────────────────────────────────
# 三项要求：① Chromium 进程在跑 ② 带 --remote-debugging-port=9222
#           ③ 带 --load-extension=…/opencli-extension
CHROMIUM_BIN="${CHROMIUM_BIN:-/usr/bin/chromium}"
OPENCLI_EXT="${HOME}/opencli-extension"
CHROMIUM_NEED_START=0

# 检查 Chromium 是否在跑且带了必要参数
CHROME_PID="$(pgrep -f "${CHROMIUM_BIN}.*remote-debugging-port" | head -1 || true)"
if [ -z "$CHROME_PID" ]; then
  CHROMIUM_NEED_START=1
  warn "Chromium 未运行"
elif ! grep -q "load-extension" /proc/$CHROME_PID/cmdline 2>/dev/null; then
  CHROMIUM_NEED_START=1
  warn "Chromium 运行中但未加载 opencli extension，将重启..."
  pkill -f "${CHROMIUM_BIN}" 2>/dev/null || true
  sleep 2
fi

if [ "$CHROMIUM_NEED_START" -eq 1 ]; then
  if ! xdpyinfo -display :1 &>/dev/null 2>&1; then
    warn "VNC display :1 不可用，无法启动真实浏览器（Chromium 将在 VNC 启动后自动加载）"
  else
    warn "正在以正确参数启动 Chromium..."
    CHROME_CMD="${CHROMIUM_BIN} \
      --remote-debugging-port=9222 \
      --start-fullscreen \
      --no-first-run \
      --no-default-browser-check \
      --no-sandbox \
      --load-extension=${OPENCLI_EXT}"
    DISPLAY=:1 XAUTHORITY=/root/.Xauthority setsid $CHROME_CMD &>/dev/null &
    # 同步更新 autostart desktop，保证重启后也对
    AUTOSTART="/root/.config/autostart/chromium.desktop"
    if [ -f "$AUTOSTART" ]; then
      sed -i "s|^Exec=.*|Exec=${CHROME_CMD}|" "$AUTOSTART"
    fi
    # 等待 9222 就绪（最多 15s）
    for i in $(seq 1 15); do
      curl -s --max-time 1 http://localhost:9222/json/version &>/dev/null && break
      sleep 1
    done
    ok "Chromium 已启动（带 opencli extension + 9222）"
  fi
else
  ok "Chromium 运行中（带 opencli extension + 9222）"
fi

# opencli extension 连接检查
DOCTOR_OUT="$(opencli doctor 2>/dev/null || true)"
if echo "$DOCTOR_OUT" | grep -q "Extension: connected"; then
  ok "opencli extension 已连接"
elif [ "$CHROMIUM_NEED_START" -eq 1 ]; then
  # 刚启动的 Chromium，extension 需要更多时间初始化
  sleep 5
  if opencli doctor 2>/dev/null | grep -q "Extension: connected"; then
    ok "opencli extension 已连接"
  else
    warn "extension 未连接，请在 VNC 中确认 Chromium 已加载扩展"
  fi
else
  warn "extension 未连接（Chromium 在跑但 extension 无响应，请在 VNC 中手动检查）"
fi

# ── 3. 搜索适配器 ─────────────────────────────────────────
step "4/5" "搜索适配器"

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
step "5/5" "网盘挂载"

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
