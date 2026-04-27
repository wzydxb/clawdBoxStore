#!/usr/bin/env python3
"""
kb_entities.py — 知识库实体图谱管理

用法：
  kb_entities.py <mount_path> --list          # 输出待提取文件内容（供LLM提取实体）
  kb_entities.py <mount_path> --write <json>  # 接收LLM提取结果，写入entities.json
  kb_entities.py <mount_path> --read          # 输出压缩实体表（供context注入）
  kb_entities.py <mount_path> --update <file> # 单文件增量更新实体
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime

ENTITIES_FILE = "entities.json"
INDEX_DIR = ".hermes-index"
MAX_LIST_FILES = 20
MAX_CONTENT_CHARS = 3000
MAX_READ_ENTITIES = 100


def get_index_dir(mount_path):
    return os.path.join(mount_path, INDEX_DIR)


def get_entities_path(mount_path):
    return os.path.join(get_index_dir(mount_path), ENTITIES_FILE)


def get_db_path(mount_path):
    return os.path.join(get_index_dir(mount_path), "index.db")


def load_entities(mount_path):
    path = get_entities_path(mount_path)
    if not os.path.exists(path):
        return {"updated": None, "entities": {}, "relations": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_entities(mount_path, data):
    path = get_entities_path(mount_path)
    data["updated"] = datetime.now().isoformat(timespec="seconds")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_list(mount_path, target_file=None):
    """输出待提取文件内容，供LLM提取实体。优先输出未提取过的新文件。"""
    db_path = get_db_path(mount_path)
    if not os.path.exists(db_path):
        print("ERROR: index.db 不存在，请先运行 kb_index.py --init")
        sys.exit(1)

    existing = load_entities(mount_path)
    extracted_files = set()
    for ent in existing["entities"].values():
        extracted_files.update(ent.get("files", []))

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if target_file:
        cur.execute(
            "SELECT path, name, content FROM files WHERE path = ? OR name = ?",
            (target_file, os.path.basename(target_file)),
        )
    else:
        cur.execute("SELECT path, name, content FROM files ORDER BY rowid DESC")

    rows = cur.fetchall()
    conn.close()

    # 优先未提取过的文件
    new_rows = [r for r in rows if r[1] not in extracted_files]
    old_rows = [r for r in rows if r[1] in extracted_files]
    ordered = new_rows + old_rows

    output = []
    for path, name, content in ordered[:MAX_LIST_FILES]:
        truncated = (content or "")[:MAX_CONTENT_CHARS]
        output.append({"file": name, "path": path, "content": truncated})

    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_write(mount_path, json_input):
    """接收LLM提取的实体JSON，增量合并写入entities.json。"""
    try:
        new_data = json.loads(json_input)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON解析失败: {e}")
        sys.exit(1)

    existing = load_entities(mount_path)

    # 合并实体（不覆盖已有，只追加新实体和更新文件列表）
    for name, info in new_data.get("entities", {}).items():
        if name not in existing["entities"]:
            existing["entities"][name] = info
        else:
            # 合并文件列表
            old_files = set(existing["entities"][name].get("files", []))
            new_files = set(info.get("files", []))
            existing["entities"][name]["files"] = list(old_files | new_files)
            # 更新 last_seen（取较新的）
            old_seen = existing["entities"][name].get("last_seen", "")
            new_seen = info.get("last_seen", "")
            if new_seen > old_seen:
                existing["entities"][name]["last_seen"] = new_seen

    # 合并关系（去重）
    existing_rels = {
        (r["from"], r["rel"], r["to"]) for r in existing.get("relations", [])
    }
    for rel in new_data.get("relations", []):
        key = (rel.get("from"), rel.get("rel"), rel.get("to"))
        if key not in existing_rels:
            existing["relations"].append(rel)
            existing_rels.add(key)

    save_entities(mount_path, existing)
    entity_count = len(existing["entities"])
    file_count = len(
        {f for e in existing["entities"].values() for f in e.get("files", [])}
    )
    print(f"entities.json 已更新：{entity_count} 个实体，覆盖 {file_count} 个文件")


def cmd_read(mount_path):
    """输出压缩实体表，供context注入。格式：实体名 → 文件1, 文件2"""
    data = load_entities(mount_path)
    entities = data.get("entities", {})

    if not entities:
        # 无输出，调用方跳过注入
        sys.exit(0)

    # 按 last_seen 降序排序，取前 MAX_READ_ENTITIES 个
    sorted_ents = sorted(
        entities.items(),
        key=lambda x: x[1].get("last_seen", ""),
        reverse=True,
    )[:MAX_READ_ENTITIES]

    updated = data.get("updated", "")[:10]  # 只取日期部分
    file_count = len(
        {f for e in entities.values() for f in e.get("files", [])}
    )
    print(f"[知识库实体索引·共{len(entities)}实体{file_count}文件·{updated}]")
    for name, info in sorted_ents:
        files = ", ".join(info.get("files", []))
        print(f"{name} → {files}")


def cmd_update(mount_path, target_file):
    """单文件增量更新：输出该文件内容供LLM提取，结果通过 --write 写回。"""
    cmd_list(mount_path, target_file=target_file)


def main():
    parser = argparse.ArgumentParser(description="知识库实体图谱管理")
    parser.add_argument("mount_path", help="网盘挂载路径")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="输出待提取文件内容")
    group.add_argument("--write", metavar="JSON", help="写入LLM提取的实体JSON")
    group.add_argument("--read", action="store_true", help="输出压缩实体表")
    group.add_argument("--update", metavar="FILE", help="单文件增量更新")
    args = parser.parse_args()

    mount_path = os.path.expanduser(args.mount_path)
    if not os.path.exists(mount_path):
        print(f"ERROR: 路径不存在: {mount_path}")
        sys.exit(1)

    if args.list:
        cmd_list(mount_path)
    elif args.write:
        cmd_write(mount_path, args.write)
    elif args.read:
        cmd_read(mount_path)
    elif args.update:
        cmd_update(mount_path, args.update)


if __name__ == "__main__":
    main()
