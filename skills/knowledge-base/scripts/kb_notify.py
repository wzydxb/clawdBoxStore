#!/usr/bin/env python3
"""
kb_notify.py — hermes cron --script 用
读取 /tmp/kb_pending_summary，有内容则：
1. 从 state.db 取最近活跃的 weixin user_id，动态更新 cron deliver
2. 输出 prompt 触发 agent 主动推送
无内容则退出（cron 不触发）。
"""
import os, sys, sqlite3, subprocess

PENDING = "/tmp/kb_pending_summary"
STATE_DB = os.path.expanduser("~/.hermes/state.db")
CRON_JOB_ID = "3d03d9db2a03"

if not os.path.exists(PENDING):
    sys.exit(0)

content = open(PENDING).read().strip()
if not content:
    sys.exit(0)

open(PENDING, 'w').close()

# 取最近活跃的 weixin user_id
try:
    db = sqlite3.connect(STATE_DB)
    row = db.execute(
        "SELECT s.user_id FROM messages m "
        "JOIN sessions s ON m.session_id = s.id "
        "WHERE s.source='weixin' AND s.user_id IS NOT NULL "
        "ORDER BY m.timestamp DESC LIMIT 1"
    ).fetchone()
    if row:
        deliver = f"weixin:{row[0]}"
        subprocess.run(
            ["hermes", "cron", "edit", CRON_JOB_ID, "--deliver", deliver],
            capture_output=True
        )
except Exception:
    pass

print(f"""我注意到知识库有新文件变动：

{content}

请：
1. 用 skill_view("knowledge-base/kb-index") 确认最新索引状态
2. 读取新文件摘要（最多3句话）
3. 主动推送给用户，格式：
   📂 我看到你上传了[文件名]。
   [一句话核心内容]
   要我[具体动作：分析/对比/提炼/归档]吗？
""")
