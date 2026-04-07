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


def main() -> int:
    parser = argparse.ArgumentParser(description='Resolve style and component assets for ppt-studio')
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    style_resolution = {
        'style_mode': 'template-first',
        'fallback_style': 'whiteboard',
        'theme': plan.get('theme'),
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
