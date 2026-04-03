#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "clawdbox-ppt-nano/1.0"


def search_commons_image(query: str) -> str:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "5",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch a strong related fallback background image from the web")
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_url = search_commons_image(args.query)
    download_and_convert(image_url, output_path)
    print(f"MEDIA:{output_path}")
    print(f"SOURCE_URL:{image_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
