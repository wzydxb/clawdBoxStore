#!/usr/bin/env python3
"""
kb_notify.py — hermes cron --script 用
读取 /tmp/kb_pending_summary，有内容则：
1. 从 state.db 取最近活跃的 weixin user_id，动态更新 cron deliver
2. 输出 prompt 触发系统主动推送
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

print(f"""我注意到上传原始资料有新文件需要整理：

{content}

请立即处理：
skill_view("knowledge-base/kb-inbox")

按 kb-inbox 流程处理 上传原始资料/ 内**所有**文件（不只是第一个）：
1. 列出 上传原始资料/ 根目录全部文件
2. zip 解压到主目录临时区，不在 上传原始资料/ 内解压
3. 逐一归类、清洗、入库
4. 处理完后清空 inbox
5. 向用户报告处理结果
""")
