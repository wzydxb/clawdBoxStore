#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def component_for_slide(slide: dict) -> str:
    if slide.get("page_type") == "chart":
        return "chart"
    if slide.get("page_type") == "navigation":
        return "flowchart"
    if slide.get("page_type") == "cover":
        return "hero"
    if slide.get("page_type") == "closing":
        return "closing"
    title = str(slide.get("title", ""))
    purpose = str(slide.get("purpose", ""))
    if any(word in title + purpose for word in ["场景", "分类", "矩阵", "应用"]):
        return "card-grid"
    return "content-card"


def reference_for_slide(style: dict, slide: dict) -> str:
    refs = style.get("refs", {})
    page_type = slide.get("page_type", "content")
    return refs.get(page_type) or refs.get("content") or ""


def build_cover_prompt(theme: str, keywords: list[str], style_name: str) -> str:
    keyword_text = "、".join(keywords)
    return f"围绕主题“{theme}”生成首页主视觉背景图，核心主题包含：{keyword_text}。风格遵循 {style_name}，画面需要可作为 PPT 首页背景，突出主题气质并为整套页面提供统一视觉锚点。"


def build_slide_prompt(style: dict, slide: dict, cover_prompt: str) -> str:
    style_prompts = style.get("style_prompts", {})
    prompt_prefix = style_prompts.get(slide.get("page_type")) or style_prompts.get("content") or style.get("base_instruction", "")
    key_points = slide.get("key_points") or []
    points_text = "；".join(key_points) if key_points else slide.get("purpose", "")
    return f"{prompt_prefix}\n\n本页标题：{slide.get('title')}\n本页目的：{slide.get('purpose')}\n本页组件：{slide.get('component_type')}\n关键信息：{points_text}\n首页视觉锚点：{cover_prompt}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Select components and prompts for each slide")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--styles", required=True)
    parser.add_argument("--style", default="whiteboard")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    styles = json.loads(Path(args.styles).read_text(encoding="utf-8"))
    styles_map = styles.get("styles", {})
    style_key = args.style if args.style in styles_map else styles.get("default_style", "whiteboard")
    style = styles_map[style_key]

    cover_prompt = build_cover_prompt(brief.get("theme", "未命名主题"), brief.get("theme_keywords", []), style.get("name", style_key))
    slides = []
    for slide in plan.get("slides", []):
        enriched = dict(slide)
        enriched["component_type"] = component_for_slide(slide)
        enriched["reference_image"] = reference_for_slide(style, slide)
        enriched["selection_reason"] = f"page_type={slide.get('page_type')} -> component={enriched['component_type']}"
        enriched["final_prompt"] = build_slide_prompt(style, enriched, cover_prompt)
        slides.append(enriched)

    render_plan = {
        "theme": brief.get("theme"),
        "style": style_key,
        "global_style_lock": {
            "cover_prompt": cover_prompt,
            "style_name": style.get("name", style_key),
            "style_description": style.get("description", ""),
        },
        "slides": slides,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(render_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
