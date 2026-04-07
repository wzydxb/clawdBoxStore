#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text_arg(raw: str | None, file_path: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding='utf-8').strip()
    return (raw or '').strip()


def build_plan(theme: str, research_text: str, audience: str, slides: int, template_id: str | None) -> dict:
    if template_id == 'market-analysis-report':
        pages = [
            {'index': 1, 'title': theme, 'type': 'cover', 'purpose': '封面与主题建立'},
            {'index': 2, 'title': '目录', 'type': 'content', 'purpose': '展示结构总览'},
            {'index': 3, 'title': '市场分析', 'type': 'content', 'purpose': '章节引入'},
            {'index': 4, 'title': '市场机会与分层', 'type': 'chart', 'purpose': '分层市场与占比'},
            {'index': 5, 'title': '重点城市与区域', 'type': 'chart', 'purpose': '地域数据'},
            {'index': 6, 'title': '竞争格局', 'type': 'content', 'purpose': '竞品与对比'},
            {'index': 7, 'title': '客户分析', 'type': 'content', 'purpose': '章节引入'},
            {'index': 8, 'title': '用户画像', 'type': 'content', 'purpose': '客户画像卡片'},
            {'index': 9, 'title': '核心数据判断', 'type': 'chart', 'purpose': '关键指标与趋势'},
            {'index': 10, 'title': '总结与建议', 'type': 'content', 'purpose': '行动建议'},
            {'index': 11, 'title': '感谢聆听', 'type': 'closing', 'purpose': '致谢页'},
        ]
    elif template_id == 'employee-training':
        pages = [
            {'index': 1, 'title': theme, 'type': 'cover', 'purpose': '培训封面'},
            {'index': 2, 'title': '目录', 'type': 'content', 'purpose': '培训目录'},
            {'index': 3, 'title': '培训目的', 'type': 'content', 'purpose': '培训目标说明'},
            {'index': 4, 'title': '关键知识点一', 'type': 'content', 'purpose': '重点知识'},
            {'index': 5, 'title': '关键知识点二', 'type': 'content', 'purpose': '重点知识'},
            {'index': 6, 'title': '流程与规范', 'type': 'navigation', 'purpose': '流程说明'},
            {'index': 7, 'title': '案例示例', 'type': 'content', 'purpose': '案例说明'},
            {'index': 8, 'title': '风险提醒', 'type': 'content', 'purpose': '常见风险'},
            {'index': 9, 'title': '培训总结', 'type': 'content', 'purpose': '总结归纳'},
            {'index': 10, 'title': '感谢聆听', 'type': 'closing', 'purpose': '致谢页'},
        ]
    else:
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
        'template_id': template_id,
        'pages': pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Build deck plan for ppt-studio')
    parser.add_argument('--theme', required=True)
    parser.add_argument('--research-text')
    parser.add_argument('--research-file')
    parser.add_argument('--audience', default='管理层')
    parser.add_argument('--slides', type=int, default=6)
    parser.add_argument('--template-id')
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    research_text = read_text_arg(args.research_text, args.research_file)
    plan = build_plan(args.theme, research_text, args.audience, args.slides, args.template_id)
    (out_dir / 'deck_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'slide_outline.json').write_text(json.dumps(plan['pages'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out_dir / 'deck_plan.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
