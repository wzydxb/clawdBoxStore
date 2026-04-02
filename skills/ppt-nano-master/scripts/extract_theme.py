#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text_arg(raw: str | None, file_path: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    return (raw or "").strip()


def derive_theme_keywords(theme: str, research_text: str) -> list[str]:
    text = f"{theme}\n{research_text}".lower()
    keywords: list[str] = []
    mapping = [
        ("ai", ["ai", "agent", "智能", "自动化", "模型"]),
        ("科技", ["科技", "技术", "平台", "系统", "数字化"]),
        ("商务", ["市场", "商业", "落地", "客户", "企业"]),
        ("增长", ["增长", "趋势", "机会", "空间", "规模"]),
        ("场景", ["场景", "应用", "行业", "方案"]),
        ("流程", ["流程", "路径", "阶段", "链路"]),
    ]
    for label, needles in mapping:
        if any(token in text for token in needles):
            keywords.append(label)
    if not keywords:
        keywords = [theme[:12] or "主题"]
    return keywords[:6]


def build_brief(theme: str, research_text: str, audience: str, goal: str, slides: int) -> dict:
    theme_keywords = derive_theme_keywords(theme, research_text)
    core_message = theme.strip() or "主题未命名"
    narrative_arc = [
        "问题与机会",
        "市场与场景",
        "价值与路径",
        "建议与行动",
    ]
    must_include_facts = []
    for line in research_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(ch.isdigit() for ch in line) or any(word in line for word in ["增长", "市场", "客户", "案例", "趋势"]):
            must_include_facts.append(line)
        if len(must_include_facts) >= 8:
            break
    if not must_include_facts and research_text:
        must_include_facts = [part.strip() for part in research_text.split("。") if part.strip()][:5]
    return {
        "theme": core_message,
        "core_message": core_message,
        "target_audience": audience or "管理层",
        "goal": goal or "做出一版可汇报的 PPT 草稿",
        "slides": slides,
        "narrative_arc": narrative_arc,
        "must_include_facts": must_include_facts,
        "tone": "专业、简洁、可汇报",
        "risk_notes": ["无真实数据时明确标注示意数据或待补数据"],
        "theme_keywords": theme_keywords,
        "research_excerpt": research_text[:3000],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a structured deck brief from theme and research text")
    parser.add_argument("--theme", required=True)
    parser.add_argument("--research-text")
    parser.add_argument("--research-file")
    parser.add_argument("--audience", default="管理层")
    parser.add_argument("--goal", default="")
    parser.add_argument("--slides", type=int, default=8)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    research_text = read_text_arg(args.research_text, args.research_file)
    brief = build_brief(args.theme, research_text, args.audience, args.goal, args.slides)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
