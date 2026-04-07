#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def component_for_page(page: dict) -> str:
    mapping = {
        'cover': 'hero',
        'chart': 'chart',
        'navigation': 'flowchart',
        'closing': 'closing',
    }
    return mapping.get(page.get('type'), 'content-card')


def choose_template(plan: dict, templates: list[dict]) -> dict | None:
    text = (plan.get('theme', '') + ' ' + plan.get('research_text', '')).lower()
    scored = []
    for template in templates:
        score = 0
        for kw in template.get('best_for', []):
            if kw.lower() in text:
                score += 2
        category = template.get('category', '')
        if category in text:
            score += 1
        if 'ai' in text and template.get('category') == 'innovation':
            score += 3
        if any(w in text for w in ['路线', '路径', '规划']) and template.get('category') == 'roadmap':
            score += 3
        if any(w in text for w in ['汇报', '经营', '管理层', '市场']) and template.get('category') == 'business':
            score += 2
        scored.append((score, template))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] > 0 else (templates[0] if templates else None)


def main() -> int:
    parser = argparse.ArgumentParser(description='Resolve style and component assets for ppt-studio')
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    templates_path = Path(__file__).resolve().parents[1] / 'assets' / 'templates' / 'templates.json'
    templates = json.loads(templates_path.read_text(encoding='utf-8')) if templates_path.exists() else []
    selected_template = choose_template(plan, templates)
    style_resolution = {
        'style_mode': 'template-first',
        'fallback_style': 'whiteboard',
        'theme': plan.get('theme'),
        'selected_template': selected_template,
    }
    specs = []
    assets = []
    for page in plan.get('pages', []):
        component = component_for_page(page)
        specs.append({
            'index': page['index'],
            'title': page['title'],
            'page_type': page['type'],
            'component_type': component,
            'purpose': page['purpose'],
        })
        assets.append({
            'index': page['index'],
            'asset_type': component,
            'path': f"assets/slide-{page['index']:02d}.png",
        })
    (out_dir / 'style_resolution.json').write_text(json.dumps(style_resolution, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'slide_specs.json').write_text(json.dumps(specs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'slide_assets_manifest.json').write_text(json.dumps(assets, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out_dir / 'slide_specs.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
