#!/usr/bin/env python3
"""
kb_organize.py - 文件整理归档

用法：
  python3 kb_organize.py <mount_path>             # 扫描并输出归档建议（预览）
  python3 kb_organize.py <mount_path> --execute   # 确认后执行移动+重命名
  python3 kb_organize.py <mount_path> --file <path> --dest <new_path>  # 移动单个文件
"""

import sys
import os
import re
import shutil
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

SKIP_DIRS = {".hermes-index", ".DS_Store", ".Spotlight-V100", ".Trashes"}

# 业务主题关键词映射
TOPIC_RULES = [
    (["合同", "contract", "协议", "agreement"], "合同"),
    (["发票", "invoice", "inv", "receipt"], "发票"),
    (["报告", "report", "汇报", "总结", "summary"], "报告"),
    (["方案", "proposal", "plan", "计划"], "方案"),
    (["会议", "meeting", "纪要", "minutes"], "会议纪要"),
    (["财务", "finance", "预算", "budget", "账单"], "财务"),
    (["截图", "screenshot", "截屏"], "截图"),
    (["照片", "photo", "img", "image"], "图片"),
]


# ── 推断文件主题 ──────────────────────────────────────────

def infer_topic(fname: str, content: str = "") -> str:
    text = (fname + " " + content).lower()
    for keywords, topic in TOPIC_RULES:
        if any(k in text for k in keywords):
            return topic
    # 仅靠扩展名兜底（只在 fname 有值时）
    if fname:
        ext = Path(fname).suffix.lower()
        if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"):
            return "图片"
        if ext in (".mp4", ".mov", ".avi", ".mkv"):
            return "视频"
        if ext in (".py", ".js", ".ts", ".sh", ".go"):
            return "代码"
    return ""


# ── 推断文件日期 ──────────────────────────────────────────

def infer_date(fpath: str) -> str:
    fname = Path(fpath).name
    # 文件名中的日期（优先）
    m = re.search(r'(\d{4})[.\-_]?(\d{2})[.\-_]?(\d{2})', fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # 文件修改时间
    mtime = os.path.getmtime(fpath)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


# ── 生成规范化文件名 ──────────────────────────────────────

def normalize_name(fpath: str, topic: str) -> str:
    fname = Path(fpath).name
    ext = Path(fpath).suffix
    date = infer_date(fpath)
    stem = Path(fpath).stem

    # 已经是规范格式（YYYY-MM-DD-...）则不改
    if re.match(r'\d{4}-\d{2}-\d{2}-', stem):
        return fname

    # 截图特殊处理
    if re.match(r'截屏\d{4}', stem) or re.match(r'screenshot', stem, re.I):
        return f"{date}-截图{ext}"

    return f"{date}-{topic}-{fname}"


# ── 扫描根目录散落文件 ────────────────────────────────────

def scan_unorganized(mount: str) -> list:
    result = []
    for entry in os.scandir(mount):
        if entry.is_file() and not entry.name.startswith("."):
            result.append(entry.path)
    return result


# ── 读取索引摘要 ──────────────────────────────────────────

def get_summary(mount: str, fpath: str) -> str:
    db_path = os.path.join(mount, ".hermes-index", "index.db")
    if not os.path.exists(db_path):
        return ""
    db = sqlite3.connect(db_path)
    row = db.execute("SELECT content FROM files WHERE path=?",
                     (fpath,)).fetchone()
    return (row[0] or "")[:500] if row else ""


# ── 生成归档计划 ──────────────────────────────────────────

def make_plan(mount: str, files: list) -> list:
    plan = []
    year = datetime.now().strftime("%Y")
    for fpath in files:
        fname = Path(fpath).name
        content = get_summary(mount, fpath)

        # 内容优先匹配，文件名兜底，都没有则「其他」
        topic = infer_topic("", content) or infer_topic(fname, "") or "其他"
        matched_in = "内容" if infer_topic("", content) else \
                     "文件名" if infer_topic(fname, "") else "默认"

        new_name = normalize_name(fpath, topic)
        new_path = os.path.join(mount, year, topic, new_name)
        reason = f"依据{matched_in}识别为「{topic}」"
        plan.append({"old": fpath, "new": new_path,
                     "topic": topic, "reason": reason})
    return plan


# ── 打印预览 ──────────────────────────────────────────────

def print_plan(plan: list):
    print(f"\n📋 归档建议（共 {len(plan)} 个文件）\n")
    for item in plan:
        old_name = Path(item["old"]).name
        new_rel = os.path.relpath(item["new"],
                                  os.path.dirname(os.path.dirname(item["new"])))
        print(f"📄 {old_name}")
        print(f"   → {new_rel}")
        print(f"   依据：{item['reason']}")
        print()
    print("确认执行请加 --execute 参数重新运行。")


# ── 执行移动 + 更新索引 ───────────────────────────────────

def execute_plan(mount: str, plan: list):
    db_path = os.path.join(mount, ".hermes-index", "index.db")
    db = sqlite3.connect(db_path) if os.path.exists(db_path) else None

    for item in plan:
        old_path = item["old"]
        new_path = item["new"]

        if not os.path.exists(old_path):
            print(f"[跳过] 文件不存在：{old_path}")
            continue
        if os.path.exists(new_path):
            print(f"[跳过] 目标已存在：{new_path}")
            continue

        # 创建目标目录
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        # 移动文件
        shutil.move(old_path, new_path)
        print(f"✅ {Path(old_path).name} → {os.path.relpath(new_path, mount)}")

        # 更新索引路径
        if db:
            new_name = Path(new_path).name
            db.execute("UPDATE files SET path=?, name=? WHERE path=?",
                       (new_path, new_name, old_path))
            db.execute("UPDATE meta SET path=? WHERE path=?",
                       (new_path, old_path))

        # 更新 wiki/_index.md
        index_md = os.path.join(mount, ".hermes-index", "wiki", "_index.md")
        if os.path.exists(index_md):
            content = open(index_md).read().replace(old_path, new_path)
            open(index_md, "w").write(content)

    if db:
        db.commit()
    print(f"\n完成，共移动 {len(plan)} 个文件。")


# ── 移动单个文件 ──────────────────────────────────────────

def move_single(mount: str, old_path: str, new_path: str):
    execute_plan(mount, [{"old": old_path, "new": new_path,
                          "reason": "手动指定"}])


# ── 入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="知识库文件整理归档")
    parser.add_argument("mount", help="网盘挂载路径")
    parser.add_argument("--execute", action="store_true", help="执行归档（默认仅预览）")
    parser.add_argument("--file", help="移动单个文件（配合 --dest 使用）")
    parser.add_argument("--dest", help="目标路径")
    args = parser.parse_args()

    if not os.path.exists(args.mount):
        print(f"错误：挂载路径不存在 {args.mount}")
        sys.exit(1)

    if args.file and args.dest:
        move_single(args.mount, args.file, args.dest)
    else:
        files = scan_unorganized(args.mount)
        if not files:
            print("根目录无散落文件，无需整理。")
            sys.exit(0)
        plan = make_plan(args.mount, files)
        if args.execute:
            execute_plan(args.mount, plan)
        else:
            print_plan(plan)
