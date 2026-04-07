#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def add_textbox(slide, text, x, y, w, h, font_size=22, bold=False, color=(31, 41, 55)):
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    p = frame.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(*color)
    return box


def build_pptx(plan: dict, specs: list[dict], output: Path) -> None:
    from pptx import Presentation
    from pptx.util import Inches
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    theme = plan.get('theme', '未命名主题')

    for spec in specs:
        slide = prs.slides.add_slide(blank)
        bg = slide.background.fill
        if spec['page_type'] in ('cover', 'closing'):
            bg.solid(); bg.fore_color.rgb = RGBColor(13, 23, 42)
            title_color = (255, 255, 255)
            accent = (96, 165, 250)
        else:
            bg.solid(); bg.fore_color.rgb = RGBColor(248, 250, 252)
            title_color = (15, 23, 42)
            accent = (37, 99, 235)

        if spec['page_type'] == 'cover':
            add_textbox(slide, theme, 0.8, 2.1, 11.5, 1.2, font_size=44, bold=True, color=title_color)
            add_textbox(slide, '主题汇报 / 结构规划 / 方案输出', 0.85, 3.35, 9.8, 0.5, font_size=22, color=accent)
            slide.shapes.add_shape(1, Inches(0.85), Inches(4.35), Inches(4.5), Inches(0.12)).fill.solid()
            slide.shapes[-1].fill.fore_color.rgb = RGBColor(*accent)
        elif spec['page_type'] == 'closing':
            add_textbox(slide, '感谢聆听', 0.9, 2.6, 11.0, 1.0, font_size=48, bold=True, color=title_color)
            add_textbox(slide, 'Thank You', 0.95, 3.8, 8.0, 0.6, font_size=24, color=accent)
        elif spec['component_type'] == 'chart':
            add_textbox(slide, spec['title'], 0.7, 0.5, 12, 0.6, font_size=34, bold=True, color=title_color)
            add_textbox(slide, '示意数据 / 待补真实数据', 0.8, 1.35, 4.0, 0.4, font_size=16, color=(100, 116, 139))
            for i, h in enumerate([2.4, 3.1, 4.1, 2.8]):
                shape = slide.shapes.add_shape(1, Inches(1.2 + i * 1.25), Inches(5.6 - h), Inches(0.7), Inches(h))
                shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(*accent)
            add_textbox(slide, '核心判断：先看趋势，再补真实数据校准。', 7.0, 2.0, 5.0, 1.0, font_size=24, bold=True, color=title_color)
        elif spec['component_type'] == 'flowchart':
            add_textbox(slide, spec['title'], 0.7, 0.5, 12, 0.6, font_size=34, bold=True, color=title_color)
            steps = ['识别场景', '选择路径', '试点落地', '规模复制']
            for i, step in enumerate(steps):
                x = 0.9 + i * 3.0
                card = slide.shapes.add_shape(5, Inches(x), Inches(2.7), Inches(2.2), Inches(1.2))
                card.fill.solid(); card.fill.fore_color.rgb = RGBColor(219, 234, 254)
                add_textbox(slide, step, x + 0.25, 3.05, 1.7, 0.4, font_size=18, bold=True, color=title_color)
                if i < len(steps) - 1:
                    line = slide.shapes.add_shape(13, Inches(x + 2.25), Inches(3.15), Inches(0.65), Inches(0.25))
                    line.fill.solid(); line.fill.fore_color.rgb = RGBColor(*accent)
        else:
            add_textbox(slide, spec['title'], 0.7, 0.5, 12, 0.6, font_size=34, bold=True, color=title_color)
            cards = ['关键点一', '关键点二', '关键点三']
            for i, card_text in enumerate(cards):
                x = 0.8 + i * 4.1
                card = slide.shapes.add_shape(5, Inches(x), Inches(2.0), Inches(3.5), Inches(2.8))
                card.fill.solid(); card.fill.fore_color.rgb = RGBColor(255, 255, 255)
                card.line.color.rgb = RGBColor(203, 213, 225)
                add_textbox(slide, card_text, x + 0.25, 2.35, 3.0, 0.4, font_size=20, bold=True, color=title_color)
                add_textbox(slide, spec.get('purpose', ''), x + 0.25, 3.0, 3.0, 1.2, font_size=15, color=(71, 85, 105))

    prs.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description='Render final PPTX for ppt-studio')
    parser.add_argument('--plan', required=True)
    parser.add_argument('--specs', required=True)
    parser.add_argument('--assets', required=True)
    parser.add_argument('--style-resolution')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    specs = json.loads(Path(args.specs).read_text(encoding='utf-8'))
    style_resolution = json.loads(Path(args.style_resolution).read_text(encoding='utf-8')) if args.style_resolution else {}
    build_pptx(plan, specs, out_path)
    report = {
        'plan': args.plan,
        'specs': args.specs,
        'assets': args.assets,
        'style_resolution': args.style_resolution,
        'selected_template': style_resolution.get('selected_template'),
        'output': str(out_path),
        'mode': 'template-first-mvp-python-pptx',
        'slide_count': len(specs),
    }
    (out_path.parent / 'render_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
