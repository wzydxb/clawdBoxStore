#!/usr/bin/env python3
"""
session_tail.py — 读取最近一次会话的尾部对话，供新 session 注入上下文。

用法：
  python3 session_tail.py [--max-turns 10] [--max-chars 2000]

输出：
  有内容 → 打印压缩的对话摘要（用户/助手交替）
  无内容 → 无输出（调用方跳过注入）
"""

import argparse
import glob
import json
import os
import sys

SESSIONS_DIR = os.path.expanduser("~/.hermes/sessions")


def find_previous_session(current_session_id=None):
    """找到最近的、非当前的 session 文件。"""
    pattern = os.path.join(SESSIONS_DIR, "*.jsonl")
    files = sorted(glob.glob(pattern), reverse=True)

    if not files:
        return None

    current_env = os.environ.get("HERMES_SESSION_ID", "")

    for f in files:
        basename = os.path.basename(f)
        session_id = basename.replace(".jsonl", "")
        if current_session_id and session_id == current_session_id:
            continue
        if current_env and session_id == current_env:
            continue
        # 跳过当前 session（按文件修改时间判断，最新的可能是当前）
        # 取第二新的文件
        return f

    return None


def extract_tail(filepath, max_turns=10, max_chars=2000):
    """从 session 文件提取尾部 user/assistant 对话。"""
    messages = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                role = obj.get("role", "")
                if role not in ("user", "assistant"):
                    continue
                content = obj.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict):
                            t = item.get("text", "")
                            if t:
                                parts.append(t)
                        elif isinstance(item, str):
                            parts.append(item)
                    content = "\n".join(parts)
                content = str(content).strip()
                if not content:
                    continue
                messages.append((role, content))
            except (json.JSONDecodeError, KeyError):
                continue

    if not messages:
        return None

    tail = messages[-max_turns:]

    lines = []
    total = 0
    for role, content in tail:
        label = "用户" if role == "user" else "助手"
        truncated = content[:500]
        line = f"{label}：{truncated}"
        if total + len(line) > max_chars:
            remaining = max_chars - total
            if remaining > 50:
                lines.append(f"{label}：{truncated[:remaining]}…")
            break
        lines.append(line)
        total += len(line)

    return "\n".join(lines) if lines else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--max-chars", type=int, default=2000)
    args = parser.parse_args()

    # 找最近的 session 文件列表
    pattern = os.path.join(SESSIONS_DIR, "*.jsonl")
    files = sorted(glob.glob(pattern), reverse=True)

    if len(files) < 2:
        # 只有一个或没有 session，无法取"上一个"
        sys.exit(0)

    # 最新的是当前 session，取第二个
    prev_file = files[1]

    result = extract_tail(prev_file, args.max_turns, args.max_chars)
    if result:
        session_name = os.path.basename(prev_file).replace(".jsonl", "")
        print(f"[上次对话·{session_name}]")
        print(result)


if __name__ == "__main__":
    main()
