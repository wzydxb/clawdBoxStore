#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_default_slides(brief: dict, max_slides: int) -> list[dict]:
    theme = brief.get("theme", "未命名主题")
    facts = list(brief.get("must_include_facts", []))
    slide_specs = [
        ("cover", f"{theme}", "首页主视觉 + 大标题", []),
        ("content", "核心结论", "先讲结论和价值主张", facts[:3]),
        ("content", "市场机会", "说明为什么值得做", facts[3:6]),
        ("content", "落地场景", "按场景拆分卡片矩阵", []),
        ("chart", "关键数据与趋势", "用图表或表格展示数据", facts[:4]),
        ("navigation", "落地路径", "用流程图或时间轴展示推进路径", []),
        ("content", "风险与门槛", "列风险、限制与约束", facts[4:7]),
        ("content", "建议与行动", "给出行动建议和优先级", []),
        ("closing", "感谢聆听", "尾页致谢", []),
    ]
    trimmed = slide_specs[: max(2, min(max_slides, len(slide_specs)))]
    if trimmed[-1][0] != "closing":
        trimmed[-1] = ("closing", "感谢聆听", "尾页致谢", [])
    slides = []
    for idx, (page_type, title, purpose, key_points) in enumerate(trimmed, start=1):
        text = " ".join(key_points)
        slides.append({
            "index": idx,
            "title": title,
            "purpose": purpose,
            "page_type": page_type,
            "key_points": key_points,
            "data_flag": page_type == "chart" or any(ch.isdigit() for ch in text),
            "flow_flag": page_type == "navigation",
        })
    return slides


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan slide structure from deck brief")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--max-slides", type=int, default=8)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    plan = {
        "theme": brief.get("theme"),
        "target_audience": brief.get("target_audience"),
        "slides": build_default_slides(brief, args.max_slides),
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
