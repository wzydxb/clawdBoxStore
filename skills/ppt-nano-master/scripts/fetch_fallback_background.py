#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "clawdbox-ppt-nano/1.0"
MAX_WEB_RETRIES = 2
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


def classify_theme(query: str) -> str:
    text = query.lower()
    if any(word in text for word in ["ai", "agent", "模型", "科技", "技术", "平台", "数字化"]):
        return "tech"
    if any(word in text for word in ["医疗", "医院", "健康", "药"]):
        return "medical"
    if any(word in text for word in ["教育", "学校", "课程", "开学"]):
        return "education"
    if any(word in text for word in ["环保", "森林", "自然", "绿"]):
        return "nature"
    return "business"


def search_commons_image(query: str) -> str:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url",
    }
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if infos:
            image_url = infos[0].get("url", "")
            if re.search(r"\.(jpg|jpeg|png)$", image_url, re.I):
                return image_url
    raise RuntimeError("no suitable commons image found")


def download_and_convert(url: str, output_path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    tmp_path = output_path.with_suffix(".tmp")
    tmp_path.write_bytes(raw)
    with Image.open(tmp_path) as image:
        image.convert("RGB").save(output_path, format="JPEG", quality=95)
    tmp_path.unlink(missing_ok=True)


def derive_keywords(query: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"[，,、；;\s]+", query) if part.strip()]
    return parts[:4]


def create_cover_page(theme_kind: str, title: str, output_path: Path) -> None:
    size = (1536, 1024)
    palettes = {
        "tech": ((8, 18, 42), (34, 74, 160), (255, 255, 255), (99, 179, 237)),
        "medical": ((231, 243, 255), (147, 197, 253), (18, 52, 86), (59, 130, 246)),
        "education": ((249, 250, 251), (253, 224, 71), (17, 24, 39), (217, 119, 6)),
        "nature": ((22, 101, 52), (134, 239, 172), (255, 255, 255), (190, 242, 100)),
        "business": ((24, 24, 27), (96, 165, 250), (255, 255, 255), (251, 191, 36)),
    }
    start, end, text_color, accent = palettes.get(theme_kind, palettes["business"])
    image = Image.new("RGB", size, start)
    draw = ImageDraw.Draw(image)
    w, h = size
    for y in range(h):
        ratio = y / max(1, h - 1)
        color = tuple(int(start[i] * (1 - ratio) + end[i] * ratio) for i in range(3))
        draw.line((0, y, w, y), fill=color)
    for i in range(0, w, 120):
        draw.line((i, 0, i, h), fill=(255, 255, 255, 18), width=1)
    for i in range(0, h, 120):
        draw.line((0, i, w, i), fill=(255, 255, 255, 12), width=1)
    draw.rounded_rectangle((80, 80, w - 80, h - 80), radius=42, outline=(255, 255, 255), width=2)

    # stronger theme motifs
    if theme_kind == "tech":
        for x in range(180, 1320, 180):
            draw.ellipse((x, 520, x + 18, 538), fill=accent)
            draw.line((x + 9, 529, x + 160, 420), fill=accent, width=4)
            draw.line((x + 9, 529, x + 160, 638), fill=accent, width=4)
        draw.rectangle((980, 180, 1260, 360), outline=accent, width=3)
        draw.line((1010, 220, 1230, 220), fill=accent, width=2)
        draw.line((1010, 260, 1180, 260), fill=accent, width=2)
    elif theme_kind == "medical":
        draw.ellipse((1040, 180, 1260, 400), outline=accent, width=4)
        draw.line((1150, 200, 1150, 380), fill=accent, width=8)
        draw.line((1060, 290, 1240, 290), fill=accent, width=8)
    elif theme_kind == "business":
        bars = [220, 300, 380, 460]
        heights = [180, 250, 330, 420]
        for x, top in zip(bars, heights):
            draw.rounded_rectangle((1040 + x - 220, top, 1090 + x - 220, 520), radius=8, fill=accent)
        draw.line((1060, 520, 1310, 360), fill=(255,255,255), width=5)
    elif theme_kind == "education":
        draw.rectangle((1020, 180, 1280, 360), outline=accent, width=4)
        draw.line((1035, 210, 1265, 210), fill=accent, width=2)
        draw.line((1035, 250, 1200, 250), fill=accent, width=2)
        draw.line((1035, 290, 1220, 290), fill=accent, width=2)
    elif theme_kind == "nature":
        draw.ellipse((1080, 180, 1230, 330), outline=accent, width=4)
        draw.line((1155, 330, 1155, 430), fill=accent, width=6)
        draw.line((1155, 360, 1110, 410), fill=accent, width=4)
        draw.line((1155, 360, 1200, 410), fill=accent, width=4)

    font_path = choose_font()
    title_font = ImageFont.truetype(font_path, 86) if font_path else ImageFont.load_default()
    sub_font = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default()
    chip_font = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()

    draw.text((120, 180), title, font=title_font, fill=text_color)
    draw.text((124, 300), "市场分析 / 方案汇报 / 趋势判断", font=sub_font, fill=accent)

    keywords = derive_keywords(title)
    x = 126
    y = 410
    for kw in keywords:
        bbox = draw.textbbox((x, y), kw, font=chip_font)
        draw.rounded_rectangle((bbox[0]-18, bbox[1]-10, bbox[2]+18, bbox[3]+10), radius=18, fill=(*accent[:3], 180) if isinstance(accent, tuple) else (99,179,237,180))
        draw.text((x, y), kw, font=chip_font, fill=(255,255,255))
        x = bbox[2] + 48

    draw.text((120, 860), "Clawdbox PPT fallback cover", font=chip_font, fill=(230,230,230))
    image.save(output_path, format="JPEG", quality=95)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch or synthesize a fallback cover/background image")
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    last_error: str | None = None
    for _ in range(MAX_WEB_RETRIES):
        try:
            image_url = search_commons_image(args.query)
            download_and_convert(image_url, output_path)
            print(f"MEDIA:{output_path}")
            print(f"SOURCE_URL:{image_url}")
            return 0
        except Exception as exc:
            last_error = str(exc)

    theme_kind = classify_theme(args.query)
    create_cover_page(theme_kind, args.query, output_path)
    print(f"MEDIA:{output_path}")
    print(f"FALLBACK_THEME:{theme_kind}")
    if last_error:
        print(f"FALLBACK_REASON:{last_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
