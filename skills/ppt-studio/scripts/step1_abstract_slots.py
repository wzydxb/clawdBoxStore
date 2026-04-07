#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PLACEHOLDER_PATTERNS = [
    '描述相关的信息以解释你的标题',
    '输入相关的描述信息以解释你的标题',
    '请在此处编辑文字',
    '公司名字',
    '主讲人：李天天',
]


def infer_semantic_type(text: str, shape_name: str, order: int) -> str:
    lower = text.lower()
    if order == 0 or 'title' in shape_name.lower():
        return 'text.title'
    if any(token in text for token in ['目录', '总结', '感谢观看', '感谢聆听']):
        return 'text.title'
    if any(token in text for token in PLACEHOLDER_PATTERNS):
        return 'text.body'
    if any(token in text for token in ['市场', '客户', '培训目的', '风险', '建议']):
        return 'text.body'
    return 'text.body'


def build_slots(slide: dict) -> list[dict]:
    slots = []
    for idx, shape in enumerate(slide.get('text_shapes', [])):
        slots.append({
            'slot_key': f'slot_{idx+1}',
            'semantic_type': infer_semantic_type(shape.get('text',''), shape.get('name',''), idx),
            'required': idx == 0,
            'cardinality': 'one',
            'shape_name': shape.get('name',''),
            'shape_id': shape.get('shape_id'),
            'render_rules': {
                'clear_placeholder': True,
                'placeholder_hit': any(token in shape.get('text','') for token in PLACEHOLDER_PATTERNS),
            }
        })
    return slots


def main() -> int:
    parser = argparse.ArgumentParser(description='Abstract template inventory into generic slot schema suggestions')
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--template-id', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    inventory = json.loads(Path(args.inventory).read_text(encoding='utf-8'))
    result = {
        'template_id': args.template_id,
        'slides': []
    }
    for slide in inventory.get('slides', []):
        result['slides'].append({
            'slide_key': f"slide_{slide['slide_number']}",
            'slide_number': slide['slide_number'],
            'role': 'unknown',
            'slots': build_slots(slide),
        })
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
