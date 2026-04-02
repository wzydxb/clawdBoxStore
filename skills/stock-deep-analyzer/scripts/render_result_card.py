#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_IMAGE_TOOL = "/root/.openclaw/workspace/skills/clawdbox-image-gen/scripts/gen.py"
DEFAULT_PYTHON = "/root/.openclaw/venvs/ppt/bin/python"
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]


def choose_font() -> str | None:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def run_image_tool(prompt: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        DEFAULT_PYTHON,
        DEFAULT_IMAGE_TOOL,
        "--prompt", prompt,
        "--size", "1024x1536",
        "--out-dir", str(out_dir),
        "--no-watermark",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "image tool failed")
    pngs = sorted(out_dir.glob("*.png"))
    if not pngs:
        raise RuntimeError("no card background generated")
    return pngs[0]


def wrap_text(text: str, width: int) -> list[str]:
    chars = list(text.strip())
    lines: list[str] = []
    current = ""
    for ch in chars:
        if len(current + ch) > width:
            lines.append(current)
            current = ch
        else:
            current += ch
    if current:
        lines.append(current)
    return lines


def render_overlay(bg_path: Path, output_path: Path, title: str, conclusion: str, numbers: list[str], risk: str, action: str, supports: list[str]) -> None:
    image = Image.open(bg_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = image.size
    draw.rounded_rectangle((60, 80, w - 60, h - 80), radius=36, fill=(10, 18, 32, 185))
    font_path = choose_font()
    title_font = ImageFont.truetype(font_path, 52) if font_path else ImageFont.load_default()
    body_font = ImageFont.truetype(font_path, 30) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()

    y = 130
    draw.text((100, y), title, font=title_font, fill=(255, 255, 255, 255))
    y += 90
    draw.text((100, y), f"结论：{conclusion}", font=body_font, fill=(255, 209, 102, 255))
    y += 80
    if numbers:
        draw.text((100, y), "关键数字：" + "  |  ".join(numbers[:4]), font=small_font, fill=(210, 225, 255, 255))
        y += 60
    draw.text((100, y), f"风险等级：{risk}", font=body_font, fill=(248, 113, 113, 255))
    y += 60
    draw.text((100, y), f"动作建议：{action}", font=body_font, fill=(134, 239, 172, 255))
    y += 80
    draw.text((100, y), "支撑点：", font=body_font, fill=(255, 255, 255, 255))
    y += 50
    for item in supports[:3]:
        for line in wrap_text(item, 26):
            draw.text((130, y), f"• {line}", font=small_font, fill=(220, 228, 255, 240))
            y += 34
        y += 10

    composed = Image.alpha_composite(image, overlay).convert("RGB")
    composed.save(output_path, format="PNG")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a stock deep analysis result card image")
    parser.add_argument("--title", required=True)
    parser.add_argument("--conclusion", required=True)
    parser.add_argument("--numbers", default="")
    parser.add_argument("--risk", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--supports", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    temp_dir = out_path.parent / f".{out_path.stem}-bg"
    bg_prompt = f"为投资分析结果卡片生成专业、简洁、可信赖的金融信息背景图，主题：{args.title}，风格稳重、专业、清晰，适合叠加结论和关键数字。"
    bg_path = run_image_tool(bg_prompt, temp_dir)
    numbers = [item.strip() for item in args.numbers.split("|") if item.strip()]
    supports = [item.strip() for item in args.supports.split("|") if item.strip()]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_overlay(bg_path, out_path, args.title, args.conclusion, numbers, args.risk, args.action, supports)
    print(f"CARD:{out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
