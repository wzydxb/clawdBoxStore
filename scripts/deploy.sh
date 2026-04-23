#!/bin/bash
# deploy.sh — 部署 hermes-opc 到目标盒子
# 用法: ./scripts/deploy.sh <host>
# 示例: ./scripts/deploy.sh root@192.168.10.130
#       ./scripts/deploy.sh root@192.168.10.130 --reset-user   # 强制重置用户数据

set -euo pipefail

TARGET="${1:-}"
RESET_USER="${2:-}"
SSH_PASS="${DEPLOY_PASSWORD:-}"
H="${HERMES_HOME:-/root/.hermes}"
L="$(cd "$(dirname "$0")/.." && pwd)"
OPENCLI_BASE="${OPENCLI_HOME:-/root/.opencli}"

# ── 颜色输出 ──────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
die()  { echo -e "${RED}✗${NC} $*"; exit 1; }
step() { echo -e "\n${YELLOW}[$1]${NC} $2"; }

[ -z "$TARGET" ] && die "用法: $0 <host>  例: $0 root@192.168.10.130"

# ── SSH 辅助 ──────────────────────────────────────────────
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

# 检测认证方式：优先密钥，其次 sshpass，最后交互输入
if ssh $SSH_OPTS -o BatchMode=yes "$TARGET" true 2>/dev/null; then
  _ssh() { ssh $SSH_OPTS "$TARGET" "$@"; }
  _scp() { scp $SSH_OPTS "$@" ; }
elif command -v sshpass &>/dev/null; then
  if [ -z "$SSH_PASS" ]; then
    echo -n "请输入 $TARGET 的密码: "
    read -rs SSH_PASS; echo ""
  fi
  _ssh() { sshpass -p "$SSH_PASS" ssh $SSH_OPTS "$TARGET" "$@"; }
  _scp() { sshpass -p "$SSH_PASS" scp $SSH_OPTS "$@"; }
else
  # 无 sshpass，走交互式 ssh（需要用户手动输密码）
  _ssh() { ssh $SSH_OPTS "$TARGET" "$@"; }
  _scp() { scp $SSH_OPTS "$@"; }
fi

# ── 0. 连通性检查 ─────────────────────────────────────────
step "0/7" "检查连通性"
_ssh "hermes --version" > /dev/null 2>&1 || die "无法连接 $TARGET 或 hermes 未安装"
ok "$TARGET 可达，hermes 已安装"

# ── 1. 停止 gateway（先停再改文件，避免时序冲突）──────────
step "1/7" "停止 gateway"
_ssh "hermes gateway stop 2>/dev/null; sleep 1; echo stopped" | grep -q stopped
ok "gateway 已停止"

# ── 2. 备份现有配置 ───────────────────────────────────────
step "2/7" "备份现有配置"
TS=$(date +%Y%m%d_%H%M%S)
_ssh "
  for f in SOUL.md AGENTS.md USER.md config.yaml; do
    [ -f $H/\$f ] && cp $H/\$f $H/\${f}.bak_${TS} && echo \"backed up \$f\" || true
  done
"
ok "备份完成（后缀 .bak_${TS}）"

# ── 3. 重置 gateway 状态 + 强制新建会话 ─────────────────
step "3/7" "重置 gateway 状态"
_ssh "
  rm -f $H/state.db $H/state.db-shm $H/state.db-wal 2>/dev/null
  rm -f $H/sessions/sessions.json 2>/dev/null
  echo cleared
" | grep -q cleared
ok "gateway 状态已重置（下次对话新建会话，历史保留可检索）"

# ── 4. 推送核心配置 ───────────────────────────────────────
step "4/7" "推送核心配置"

_scp "$L/AGENTS.md"          "$TARGET:$H/AGENTS.md"
_scp "$L/config/hermes.yaml" "$TARGET:$H/config.yaml"
ok "AGENTS.md / config.yaml"

# SOUL.md + USER.md：只在未完成 onboarding 或强制重置时覆盖
ONBOARDING=$(_ssh "grep -o 'pending\|role_assigned' $H/USER.md 2>/dev/null || echo none")
if [ "$ONBOARDING" = "role_assigned" ] && [ "$RESET_USER" != "--reset-user" ]; then
  warn "SOUL.md / USER.md 已完成 onboarding，跳过覆盖（用 --reset-user 强制重置）"
  # ── patch 已有 SOUL.md（升级路径）──────────────────────
  _ssh "python3 << 'PYEOF'
import re
content = open('$H/SOUL.md').read()
changes = []

# 1. ARCHETYPE_LOCK
if 'ARCHETYPE_LOCK' not in content:
    content = content.replace('## 你的思维框架\n', '## 你的思维框架\n<!-- ARCHETYPE_LOCK: 此区域由 onboarding 写入，twin-distillation 禁止修改 -->\n')
    content = re.sub(r'(<!-- ARCHETYPE_LOCK.*?-->.*?)(## 双重角色)', lambda m: m.group(1).rstrip() + '\n<!-- /ARCHETYPE_LOCK -->\n\n' + m.group(2), content, flags=re.DOTALL)
    changes.append('ARCHETYPE_LOCK')

# 2. 历史会话检索 → fact_store
OLD_S = '先读取 ~/.hermes/MEMORY.md 查找相关话题摘要；若未找到，再调用 session_search 工具检索历史会话。'
NEW_S = '1. 先调用 fact_store(action=\"search\", query=\"<关键词>\") 查找相关记忆\n2. 若未找到，再调用 session_search 工具检索历史会话全文'
if OLD_S in content:
    content = content.replace(OLD_S, NEW_S)
    changes.append('session_search→fact_store')

# 3. 话题记忆沉淀 → fact_store
OLD_M = '把话题摘要追加写入 ~/.hermes/MEMORY.md'
NEW_M = '调用 fact_store(action=\"add\", ...) 保存话题摘要'
if OLD_M in content:
    content = content.replace(OLD_M, NEW_M)
    changes.append('MEMORY.md→fact_store')

# 4. Role Skills → Role Dir
if '- Role Skills：' in content:
    content = re.sub(r'- Role Skills：(\S+)', lambda m: '- Role Dir：' + {'pm':'product-manager','finance':'finance-manager','hr':'hr-manager','ops':'operations-manager','ceo':'ceo','data':'data-analyst'}.get(m.group(1), m.group(1)), content)
    changes.append('RoleSkills→RoleDir')

# 5. 结构：持续学习移到末尾
learn_pos = content.find('## 持续学习')
role_wf = max(content.find('## 产品经理工作流'), content.find('## CEO工作流'), content.find('## 财务经理工作流'), content.find('## HR经理工作流'), content.find('## 运营经理工作流'), content.find('## 数据分析师工作流'))
if learn_pos != -1 and role_wf != -1 and learn_pos < role_wf:
    learn_match = re.search(r'(\n## 持续学习.*?)(?=\n## |\Z)', content, re.DOTALL)
    if learn_match:
        content = content.replace(learn_match.group(1), '')
        content = content.rstrip() + learn_match.group(1).rstrip() + '\n'
        changes.append('structure_fix')

open('$H/SOUL.md', 'w').write(content)
print('patched:', changes if changes else 'already up to date')
PYEOF"
  # patch USER.md Role Skills → Role Dir
  _ssh "python3 -c \"
import re, sys
c = open('$H/USER.md').read()
if 'Role Skills' in c:
    c = re.sub(r'- Role Skills：(\S+)', lambda m: '- Role Dir：' + {'pm':'product-manager','finance':'finance-manager','hr':'hr-manager','ops':'operations-manager','ceo':'ceo','data':'data-analyst'}.get(m.group(1), m.group(1)), c)
    open('$H/USER.md','w').write(c)
    print('USER.md: Role Skills→Role Dir')
else:
    print('USER.md: already ok')
\""
  ok "SOUL.md / USER.md patch 完成"
else
  _scp "$L/SOUL.md" "$TARGET:$H/SOUL.md"
  _scp "$L/USER.md" "$TARGET:$H/USER.md"
  _scp "$L/TASKLOG.md" "$TARGET:$H/TASKLOG.md"
  ok "SOUL.md / USER.md（Onboarding Status: pending）"
fi

# ── 5. 推送 Skills ────────────────────────────────────────
step "5/7" "推送 Skills"

_ssh "mkdir -p \
  $H/skills/canvas/templates \
  $H/skills/reporting \
  $H/skills/output-format \
  $H/skills/retrospective \
  $H/skills/twin-distillation"

# canvas
_scp "$L/skills/canvas/render.py"         "$TARGET:$H/skills/canvas/render.py"
_scp "$L/skills/canvas/SKILL.md"          "$TARGET:$H/skills/canvas/SKILL.md"
_scp "$L/skills/canvas/templates/"*.html  "$TARGET:$H/skills/canvas/templates/"
ok "canvas（$(ls "$L/skills/canvas/templates/"*.html | wc -l | tr -d ' ') 个模板）"

# 基础技能
_scp "$L/skills/reporting/SKILL.md"          "$TARGET:$H/skills/reporting/SKILL.md"
_scp "$L/skills/output-format/SKILL.md"      "$TARGET:$H/skills/output-format/SKILL.md"
_scp "$L/skills/retrospective/SKILL.md"      "$TARGET:$H/skills/retrospective/SKILL.md"
_scp "$L/skills/twin-distillation/SKILL.md"  "$TARGET:$H/skills/twin-distillation/SKILL.md"
_ssh "mkdir -p $H/skills/share-bot"
_scp "$L/skills/share-bot/SKILL.md"          "$TARGET:$H/skills/share-bot/SKILL.md"
ok "reporting / output-format / retrospective / twin-distillation / share-bot"

# personas（每个角色完整 skill 包 + SOUL.md）
_ssh "mkdir -p $H/personas"
_scp -r "$L/personas/." "$TARGET:$H/personas/"
ok "personas（$(ls "$L/personas/" | wc -l | tr -d ' ') 个角色）"

# archetypes（人物认知原型，skill_view 直接加载）
_ssh "mkdir -p $H/archetypes"
_scp -r "$L/archetypes/." "$TARGET:$H/archetypes/"
ok "archetypes（$(ls "$L/archetypes/" | wc -l | tr -d ' ') 个原型）"

# archetypes symlink → skills/（让 skill_view 能直接找到原型）
_ssh "
  for d in $H/archetypes/*/; do
    name=\$(basename \"\$d\")
    [ ! -e $H/skills/\"\$name\" ] && ln -s \"\$d\" $H/skills/\"\$name\"
  done
  echo \"archetypes symlinked: \$(ls $H/skills/ | grep perspective | wc -l) perspectives\"
"
ok "archetypes → skills/ symlink 完成"

# system-setup 技能
_ssh "mkdir -p $H/skills/system-setup"
_scp "$L/skills/system-setup/SKILL.md"        "$TARGET:$H/skills/system-setup/SKILL.md"
_scp "$L/skills/system-setup/python-env.md"   "$TARGET:$H/skills/system-setup/python-env.md"
_scp "$L/skills/system-setup/opencli.md"      "$TARGET:$H/skills/system-setup/opencli.md"
_scp "$L/skills/system-setup/network-drive.md" "$TARGET:$H/skills/system-setup/network-drive.md"
ok "system-setup（4 个子文件）"

# knowledge-base 技能
_ssh "mkdir -p $H/skills/knowledge-base"
for f in "$L/skills/knowledge-base/"*.md; do
  _scp "$f" "$TARGET:$H/skills/knowledge-base/$(basename "$f")"
done
ok "knowledge-base（$(ls "$L/skills/knowledge-base/"*.md | wc -l | tr -d ' ') 个文件）"

# data-acquisition 技能（主入口 + 14个子模块）
_ssh "mkdir -p $H/skills/data-acquisition"
for f in "$L/skills/data-acquisition/"*.md; do
  _scp "$f" "$TARGET:$H/skills/data-acquisition/$(basename "$f")"
done
ok "data-acquisition（$(ls "$L/skills/data-acquisition/"*.md | wc -l | tr -d ' ') 个子模块）"

# content-writer 技能
_ssh "mkdir -p $H/skills/content-writer"
_scp "$L/skills/content-writer/SKILL.md" "$TARGET:$H/skills/content-writer/SKILL.md"
ok "content-writer skill"

# scripts（env-init.sh 等）
_ssh "mkdir -p $H/scripts"
_scp "$L/scripts/env-init.sh" "$TARGET:$H/scripts/env-init.sh"
_ssh "chmod +x $H/scripts/env-init.sh"
ok "scripts/env-init.sh"

# ── 修复 chromium.desktop（确保启动时加载 opencli extension）────
_ssh "
  DESKTOP=\$HOME/.config/autostart/chromium.desktop
  if [ -f \"\$DESKTOP\" ]; then
    if ! grep -q 'load-extension' \"\$DESKTOP\"; then
      sed -i 's|^Exec=.*|Exec=/usr/bin/chromium --start-fullscreen --remote-debugging-port=9222 --no-sandbox --load-extension=/root/opencli-extension --no-first-run|' \"\$DESKTOP\"
      echo 'chromium.desktop patched'
    else
      echo 'chromium.desktop already has extension'
    fi
  fi
"
ok "chromium.desktop extension 修复"
# 1. 去掉 chromium-vnc.service 的 ExecStartPost（每次 restart 都开新 tab 是泄漏根源）
_ssh "
  SVC=\$HOME/.config/systemd/user/chromium-vnc.service
  if [ -f \"\$SVC\" ]; then
    sed -i '/^ExecStartPost/d' \"\$SVC\"
    systemctl --user daemon-reload 2>/dev/null
    echo 'chromium-vnc ExecStartPost removed'
  fi
"
# 2. 部署 tab 清理脚本
cat > /tmp/_cleanup_tabs.sh << 'CLEANUP'
#!/bin/bash
python3 - << PYEOF
import urllib.request, json, sys
try:
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json", timeout=5).read())
    if len(tabs) <= 2:
        sys.exit(0)
    kept = False
    closed = 0
    for t in tabs:
        tid = t.get("id", "")
        typ = t.get("type", "")
        if typ == "page" and not kept:
            kept = True
            continue
        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tid}", timeout=3)
            closed += 1
        except:
            pass
    if closed > 0:
        print(f"chrome-tab-cleanup: closed {closed} tabs")
except Exception as e:
    print(f"chrome-tab-cleanup error: {e}", file=sys.stderr)
PYEOF
CLEANUP
_scp /tmp/_cleanup_tabs.sh "$TARGET:$H/scripts/cleanup-chrome-tabs.sh"
_ssh "chmod +x $H/scripts/cleanup-chrome-tabs.sh"
# 3. 安装 systemd timer（每5分钟清理一次，clawdbox heartbeat 每10秒开一个tab）
_ssh "
  mkdir -p \$HOME/.config/systemd/user
  cat > \$HOME/.config/systemd/user/chrome-tab-cleanup.service << 'EOF'
[Unit]
Description=Clean up leaked Chrome tabs
[Service]
Type=oneshot
ExecStart=$H/scripts/cleanup-chrome-tabs.sh
EOF
  cat > \$HOME/.config/systemd/user/chrome-tab-cleanup.timer << 'EOF'
[Unit]
Description=Run Chrome tab cleanup every 5 minutes
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
EOF
  systemctl --user daemon-reload 2>/dev/null
  systemctl --user enable --now chrome-tab-cleanup.timer 2>/dev/null
  echo 'chrome-tab-cleanup timer enabled'
"
ok "Chrome tab 泄漏修复（chromium-vnc ExecStartPost 已移除 + 30min 清理 timer）"

# 4. 禁用 Chromium metrics 写盘 + 每30分钟清理 DeferredBrowserMetrics
_ssh "
  SVC=\$HOME/.config/systemd/user/chromium-vnc.service
  if [ -f \"\$SVC\" ]; then
    if ! grep -q 'disable-metrics' \"\$SVC\"; then
      sed -i 's|^ExecStart=.*chromium.*|ExecStart=/usr/bin/chromium --remote-debugging-port=9222 --start-fullscreen --no-first-run --disable-metrics --disable-metrics-reporting --metrics-recording-only --disable-field-trial-config --no-pings|' \"\$SVC\"
      systemctl --user daemon-reload 2>/dev/null
      systemctl --user restart chromium-vnc.service 2>/dev/null
      echo 'chromium-vnc metrics disabled'
    else
      echo 'chromium-vnc already has metrics disabled'
    fi
  fi

  # systemd timer 兜底：每30分钟清理一次 DeferredBrowserMetrics
  cat > /etc/systemd/system/clean-chromium-metrics.service << 'EOF'
[Unit]
Description=Clean Chromium DeferredBrowserMetrics

[Service]
Type=oneshot
ExecStart=/bin/rm -rf /root/.config/chromium/DeferredBrowserMetrics/
EOF
  cat > /etc/systemd/system/clean-chromium-metrics.timer << 'EOF'
[Unit]
Description=Clean Chromium metrics every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
EOF
  systemctl daemon-reload 2>/dev/null
  systemctl enable --now clean-chromium-metrics.timer 2>/dev/null
  echo 'clean-chromium-metrics timer enabled'
"
ok "Chromium DeferredBrowserMetrics 清理（metrics 已禁用 + 30min timer）"

# opencli 搜索适配器
_ssh "for site in baidu bing so sogou sohu tianyancha 163 qqnews; do mkdir -p ${OPENCLI_BASE}/clis/\$site; done"
for site in baidu bing so sogou sohu tianyancha; do
  _scp "$L/opencli-adapters/$site/search.js" "$TARGET:${OPENCLI_BASE}/clis/$site/search.js"
done
_scp "$L/opencli-adapters/163/search.js"    "$TARGET:${OPENCLI_BASE}/clis/163/search.js"
_scp "$L/opencli-adapters/163/hot.js"       "$TARGET:${OPENCLI_BASE}/clis/163/hot.js"
_scp "$L/opencli-adapters/qqnews/search.js" "$TARGET:${OPENCLI_BASE}/clis/qqnews/search.js"
_scp "$L/opencli-adapters/qqnews/hot.js"    "$TARGET:${OPENCLI_BASE}/clis/qqnews/hot.js"
ok "opencli 搜索适配器（baidu / bing / so / sogou / sohu / tianyancha / 163 / qqnews）"

# opencli 热榜适配器
_ssh "for site in weibo zhihu baidu douyin toutiao; do mkdir -p ${OPENCLI_BASE}/clis/\$site; done"
for site in weibo zhihu douyin toutiao; do
  _scp "$L/opencli-adapters/$site/hot.js" "$TARGET:${OPENCLI_BASE}/clis/$site/hot.js"
done
_scp "$L/opencli-adapters/baidu/hot.js" "$TARGET:${OPENCLI_BASE}/clis/baidu/hot.js"
ok "opencli 热榜适配器（weibo / zhihu / baidu / douyin / toutiao）"

# ── 6. 检查 playwright ────────────────────────────────────
step "6/7" "检查 playwright + 记忆配置"

# 只检查 hermes venv（agent 跑在 venv 里，系统级不需要）
VENV_PY="$H/hermes-agent/venv/bin/python3"
VENV_PLAYWRIGHT=$(_ssh "[ -x $VENV_PY ] && $VENV_PY -c 'from playwright.sync_api import sync_playwright; print(\"OK\")' 2>/dev/null || echo NO")
if [ "$VENV_PLAYWRIGHT" != "OK" ]; then
  warn "hermes venv 缺少 playwright，正在安装..."
  _ssh "SITE=\$($VENV_PY -c 'import site; print(site.getsitepackages()[0])') && python3 -m pip install --target=\$SITE playwright -q 2>&1 | tail -1"
  ok "hermes venv playwright 已安装"
else
  ok "hermes venv playwright 已就绪"
fi

# 确保 playwright chromium 二进制已安装（canvas 渲染引擎依赖）
CHROMIUM_OK=$(_ssh "ls ~/.cache/ms-playwright/chromium-* 2>/dev/null | head -1 || echo MISSING")
if [ "$CHROMIUM_OK" = "MISSING" ]; then
  warn "playwright chromium 未安装，正在下载（约2分钟）..."
  _ssh "$VENV_PY -m playwright install chromium 2>&1 | tail -2"
  ok "playwright chromium 安装完成"
else
  ok "playwright chromium 已就绪"
fi

# 启用 holographic 本地记忆（零依赖，会话结束自动提取事实）
_ssh "hermes config set memory.provider holographic 2>/dev/null; hermes config set plugins.hermes-memory-store.auto_extract true 2>/dev/null; true"
ok "holographic 记忆已启用（auto_extract）"

# ── 7. 启动 gateway ───────────────────────────────────────
step "7/7" "启动 gateway"
# 注入 --yolo 跳过危险命令审批（写 dotfile 等操作不需要人工确认）
_ssh "sed -i 's|hermes_cli.main gateway run --replace.*|hermes_cli.main --yolo gateway run --replace|' \$HOME/.config/systemd/user/hermes-gateway.service 2>/dev/null; systemctl --user daemon-reload 2>/dev/null; true"
_ssh "hermes gateway start 2>&1 | tail -1"
sleep 3
STATUS=$(_ssh "hermes gateway status 2>&1 | grep -o 'active (running)\|failed\|inactive' | head -1")
if [ "$STATUS" = "active (running)" ]; then
  ok "gateway 运行中"
else
  die "gateway 启动失败，状态：$STATUS\n请在盒子上运行 'hermes gateway run' 查看详细错误"
fi

# ── 完成 ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  部署完成：$TARGET${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
_ssh "
  echo '  SOUL.md   :' \$(head -1 $H/SOUL.md)
  echo '  Onboarding:' \$(grep 'Onboarding Status' $H/USER.md | awk -F': ' '{print \$2}')
  echo '  Skills    :' \$(find $H/skills -name 'SKILL.md' | wc -l) 个
  echo '  Personas  :' \$(find $H/personas -maxdepth 1 -mindepth 1 -type d | wc -l) 个角色
  echo '  Templates :' \$(ls $H/skills/canvas/templates/*.html 2>/dev/null | wc -l) 个
  echo '  Gateway   : active (running)'
"
echo ""
echo "  用户发第一条微信消息即开始初始化引导。"
echo ""
