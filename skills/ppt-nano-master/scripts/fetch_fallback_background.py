#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "clawdbox-ppt-nano/1.0"
MAX_WEB_RETRIES = 2


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


def create_theme_background(theme_kind: str, output_path: Path) -> None:
    size = (1536, 1024)
    palettes = {
        "tech": ((8, 18, 42), (34, 74, 160)),
        "medical": ((231, 243, 255), (147, 197, 253)),
        "education": ((249, 250, 251), (253, 224, 71)),
        "nature": ((22, 101, 52), (134, 239, 172)),
        "business": ((24, 24, 27), (96, 165, 250)),
    }
    start, end = palettes.get(theme_kind, palettes["business"])
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
    image.save(output_path, format="JPEG", quality=95)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch or synthesize a fallback background image")
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
    create_theme_background(theme_kind, output_path)
    print(f"MEDIA:{output_path}")
    print(f"FALLBACK_THEME:{theme_kind}")
    if last_error:
        print(f"FALLBACK_REASON:{last_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
