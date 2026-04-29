#!/usr/bin/env python3
"""
kb_health.py - 索引健康检查

用法：
  python3 kb_health.py <mount_path>          # 检查失效索引 + 重复文件
  python3 kb_health.py <mount_path> --fix    # 自动清理失效索引
  python3 kb_health.py --all                 # 读 USER.md 检查所有网盘
"""

import sys
import os
import re
import sqlite3
import argparse


# ── 读取 USER.md 网盘配置 ─────────────────────────────────

def parse_mounts_from_user_md() -> list:
    user_md = os.path.expanduser("~/.hermes/USER.md")
    if not os.path.exists(user_md):
        return []
    content = open(user_md).read()
    return re.findall(r'挂载路径:\s*(.+)', content)


# ── 失效索引检查 ──────────────────────────────────────────

def check_orphans(mount: str, fix: bool = False) -> int:
    db_path = os.path.join(mount, ".hermes-index", "index.db")
    if not os.path.exists(db_path):
        print(f"[{mount}] 索引不存在，跳过。")
        return 0

    db = sqlite3.connect(db_path)
    stale_entries = []
    for (path,) in db.execute("SELECT path FROM meta"):
        if not os.path.exists(path):
            stale_entries.append(path)

    if not stale_entries:
        print(f"[{mount}] ✅ 无失效索引")
        return 0

    print(f"[{mount}] ⚠️  发现 {len(stale_entries)} 条失效索引：")
    for p in stale_entries:
        print(f"   - {p}")

    if fix:
        for p in stale_entries:
            db.execute("DELETE FROM files WHERE path=?", (p,))
            db.execute("DELETE FROM meta WHERE path=?", (p,))
        db.commit()
        print(f"   已清理 {len(stale_entries)} 条。")

    return len(stale_entries)


# ── 重复文件检测 ──────────────────────────────────────────

def check_duplicates(mount: str) -> int:
    db_path = os.path.join(mount, ".hermes-index", "index.db")
    if not os.path.exists(db_path):
        return 0

    db = sqlite3.connect(db_path)
    # name 存在 files 虚拟表里，用 meta 的 path 提取文件名
    rows = db.execute("""
        SELECT SUBSTR(path, INSTR(path, '/') + 1) as fname,
               COUNT(*) as cnt,
               GROUP_CONCAT(path, '|')
        FROM meta
        GROUP BY fname
        HAVING cnt > 1
        ORDER BY cnt DESC
    """).fetchall()

    if not rows:
        print(f"[{mount}] ✅ 无重复文件")
        return 0

    print(f"[{mount}] ⚠️  发现 {len(rows)} 组重复文件：")
    for name, cnt, paths in rows:
        print(f"   📄 {name}（{cnt} 份）")
        for p in paths.split("|"):
            print(f"      {p}")
    return len(rows)


# ── 索引统计 ──────────────────────────────────────────────

def print_stats(mount: str):
    db_path = os.path.join(mount, ".hermes-index", "index.db")
    if not os.path.exists(db_path):
        return

    db = sqlite3.connect(db_path)
    total = db.execute("SELECT COUNT(*) FROM meta").fetchone()[0]
    by_type = db.execute("""
        SELECT filetype, COUNT(*) FROM meta
        GROUP BY filetype ORDER BY COUNT(*) DESC LIMIT 10
    """).fetchall()
    last_indexed = db.execute(
        "SELECT MAX(indexed_at) FROM meta"
    ).fetchone()[0]

    print(f"\n[{mount}] 索引统计：")
    print(f"   总文件数：{total}")
    print(f"   最后更新：{last_indexed or '未知'}")
    print(f"   文件类型分布：")
    for ftype, cnt in by_type:
        print(f"     {ftype or '无扩展名':10s} {cnt}")


# ── 入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="知识库索引健康检查")
    parser.add_argument("mount", nargs="?", help="网盘挂载路径")
    parser.add_argument("--fix", action="store_true", help="自动清理失效索引")
    parser.add_argument("--all", action="store_true",
                        help="读取 USER.md 检查所有配置网盘")
    args = parser.parse_args()

    if args.all:
        mounts = parse_mounts_from_user_md()
        if not mounts:
            print("USER.md 中未配置知识库网盘。")
            sys.exit(1)
    elif args.mount:
        mounts = [args.mount]
    else:
        print("请指定网盘路径，或使用 --all 检查所有配置网盘。")
        sys.exit(1)

    for mount in mounts:
        mount = mount.strip()
        if not os.path.exists(mount):
            print(f"[跳过] 网盘未挂载：{mount}")
            continue
        print_stats(mount)
        check_orphans(mount, fix=args.fix)
        check_duplicates(mount)
        print()
