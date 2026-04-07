#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text_arg(raw: str | None, file_path: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding='utf-8').strip()
    return (raw or '').strip()


def build_plan(theme: str, research_text: str, audience: str, slides: int) -> dict:
    pages = [
        {'index': 1, 'title': theme, 'type': 'cover', 'purpose': '封面与主题建立'},
        {'index': 2, 'title': '核心结论', 'type': 'content', 'purpose': '先讲结论'},
        {'index': 3, 'title': '市场机会', 'type': 'chart', 'purpose': '用数据展示机会'},
        {'index': 4, 'title': '场景拆解', 'type': 'content', 'purpose': '卡片化场景'},
        {'index': 5, 'title': '落地路径', 'type': 'navigation', 'purpose': '流程与路径'},
        {'index': 6, 'title': '感谢聆听', 'type': 'closing', 'purpose': '致谢页'},
    ]
    pages = pages[:max(2, min(slides, len(pages)))]
    if pages[-1]['type'] != 'closing':
        pages[-1] = {'index': pages[-1]['index'], 'title': '感谢聆听', 'type': 'closing', 'purpose': '致谢页'}
    return {
        'theme': theme,
        'audience': audience or '管理层',
        'slides': slides,
        'research_text': research_text[:4000],
        'pages': pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Build deck plan for ppt-studio')
    parser.add_argument('--theme', required=True)
    parser.add_argument('--research-text')
    parser.add_argument('--research-file')
    parser.add_argument('--audience', default='管理层')
    parser.add_argument('--slides', type=int, default=6)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    research_text = read_text_arg(args.research_text, args.research_file)
    plan = build_plan(args.theme, research_text, args.audience, args.slides)
    (out_dir / 'deck_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'slide_outline.json').write_text(json.dumps(plan['pages'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out_dir / 'deck_plan.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
