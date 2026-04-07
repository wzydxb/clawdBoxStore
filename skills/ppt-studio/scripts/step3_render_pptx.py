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


def fill_existing_slide(slide, title: str, body: str) -> bool:
    text_shapes = []
    for shape in slide.shapes:
        if getattr(shape, 'has_text_frame', False) and shape.text_frame is not None:
            text_shapes.append(shape)
    if not text_shapes:
        return False
    text_shapes[0].text_frame.text = title
    if len(text_shapes) > 1:
        text_shapes[1].text_frame.text = body
    return True


def add_scratch_slide(prs, spec: dict, theme: str) -> None:
    from pptx.util import Inches
    from pptx.dml.color import RGBColor
    blank = prs.slide_layouts[6]
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
    elif spec['page_type'] == 'closing':
        add_textbox(slide, '感谢聆听', 0.9, 2.6, 11.0, 1.0, font_size=48, bold=True, color=title_color)
    else:
        add_textbox(slide, spec['title'], 0.7, 0.5, 12, 0.6, font_size=34, bold=True, color=title_color)
        add_textbox(slide, spec.get('purpose', ''), 0.8, 1.4, 10.5, 0.8, font_size=18, color=(71, 85, 105))


def build_pptx(plan: dict, specs: list[dict], output: Path, selected_template: dict | None, template_dir: Path) -> str:
    from pptx import Presentation
    template_path = template_dir / selected_template['file'] if selected_template else None
    mode = 'scratch-mvp-python-pptx'
    if template_path and template_path.exists():
        prs = Presentation(str(template_path))
        mode = 'template-fill-python-pptx'
    else:
        prs = Presentation()

    theme = plan.get('theme', '未命名主题')
    for idx, spec in enumerate(specs):
        body = spec.get('purpose', '')
        if idx < len(prs.slides):
            ok = fill_existing_slide(prs.slides[idx], spec['title'] if spec['page_type'] != 'cover' else theme, body)
            if ok:
                continue
        add_scratch_slide(prs, spec, theme)

    prs.save(output)
    return mode


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
    selected_template = style_resolution.get('selected_template')
    template_dir = Path(__file__).resolve().parents[1] / 'assets' / 'templates'
    mode = build_pptx(plan, specs, out_path, selected_template, template_dir)
    report = {
        'plan': args.plan,
        'specs': args.specs,
        'assets': args.assets,
        'style_resolution': args.style_resolution,
        'selected_template': selected_template,
        'output': str(out_path),
        'mode': mode,
        'slide_count': len(specs),
    }
    (out_path.parent / 'render_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
