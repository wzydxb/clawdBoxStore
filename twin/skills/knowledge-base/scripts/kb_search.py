#!/usr/bin/env python3
"""
kb_search.py - 知识库全文检索

用法：
  python3 kb_search.py "关键词" /Volumes/uploads [/Volumes/docs ...]
  python3 kb_search.py "关键词" --all   # 读 USER.md 自动检索所有配置网盘
  python3 kb_search.py "关键词" --all --limit 20
"""

import sys
import os
import sqlite3
import re
import argparse


# ── 单网盘检索 ────────────────────────────────────────────

def search_mount(mount: str, query: str, limit: int = 10) -> list:
    db_path = os.path.join(mount, ".hermes-index", "index.db")
    if not os.path.exists(db_path):
        return []
    db = sqlite3.connect(db_path)
    try:
        # trigram 要求至少3个字符，短查询降级用 LIKE
        if len(query) < 3:
            rows = db.execute("""
                SELECT path, name, content
                FROM files
                WHERE content LIKE ? OR name LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit)).fetchall()
            # 手动截取匹配片段
            results = []
            for path, name, content in rows:
                idx = content.lower().find(query.lower())
                snippet = content[max(0, idx-20):idx+60] if idx >= 0 else content[:80]
                results.append((path, name, f"...{snippet}..."))
            return results
        else:
            return db.execute("""
                SELECT path, name,
                       snippet(files, 2, '>>>', '<<<', '...', 40)
                FROM files
                WHERE files MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit)).fetchall()
    except sqlite3.OperationalError as e:
        print(f"[{mount}] 检索错误：{e}", file=sys.stderr)
        return []


# ── 读取 USER.md 网盘配置 ─────────────────────────────────

def parse_mounts_from_user_md() -> list:
    user_md = os.path.expanduser("~/.hermes/USER.md")
    if not os.path.exists(user_md):
        return []
    content = open(user_md).read()
    return re.findall(r'挂载路径:\s*(.+)', content)


# ── 多网盘并行检索 ────────────────────────────────────────

def search_all(mounts: list, query: str, limit: int = 10) -> list:
    results = []
    for mount in mounts:
        mount = mount.strip()
        if not os.path.exists(mount):
            print(f"[跳过] 网盘未挂载：{mount}", file=sys.stderr)
            continue
        rows = search_mount(mount, query, limit)
        results.extend(rows)
    return results


# ── 格式化输出 ────────────────────────────────────────────

def print_results(results: list):
    if not results:
        print("未找到相关文件。")
        return
    print(f"\n找到 {len(results)} 个相关文件：\n")
    for path, name, snippet in results:
        print(f"📄 {name}")
        print(f"   路径：{path}")
        print(f"   匹配：{snippet}")
        print()


# ── 入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="知识库全文检索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("mounts", nargs="*", help="网盘挂载路径（可多个）")
    parser.add_argument("--all", action="store_true",
                        help="读取 USER.md 检索所有配置网盘")
    parser.add_argument("--limit", type=int, default=10, help="每个网盘返回条数")
    args = parser.parse_args()

    if args.all:
        mounts = parse_mounts_from_user_md()
        if not mounts:
            print("USER.md 中未配置知识库网盘。")
            sys.exit(1)
    elif args.mounts:
        mounts = args.mounts
    else:
        print("请指定网盘路径，或使用 --all 检索所有配置网盘。")
        sys.exit(1)

    results = search_all(mounts, args.query, args.limit)
    print_results(results)
