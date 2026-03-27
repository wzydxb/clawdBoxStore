#!/usr/bin/env python3
"""龙虾智盒 AI 图片生成/编辑工具"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html import escape as html_escape
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:50] or "image"


def default_out_dir() -> Path:
    now = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    preferred = Path.home() / "Projects" / "tmp"
    base = preferred if preferred.is_dir() else Path("./tmp")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"clawdbox-image-gen-{now}"


def get_api_config():
    """获取 API 配置，优先从环境变量读取，否则从 openclaw 配置读取"""
    base_url = os.environ.get("CLAWDBOX_API_URL", "")
    api_key = os.environ.get("CLAWDBOX_API_KEY", "") or os.environ.get("X_AUTH_TOKEN", "")

    if not base_url or not api_key:
        config_paths = [
            Path.home() / ".openclaw" / "config.yaml",
            Path.home() / ".openclaw" / "config.yml",
        ]
        for cp in config_paths:
            if cp.exists():
                try:
                    content = cp.read_text()
                    for line in content.split("\n"):
                        line = line.strip()
                        if not base_url and ("baseUrl" in line or "base_url" in line):
                            val = line.split(":", 1)[-1].strip().strip("'\"")
                            if val:
                                base_url = val
                        if not api_key and ("apiKey" in line or "x-auth-token" in line or "token" in line):
                            val = line.split(":", 1)[-1].strip().strip("'\"")
                            if val and len(val) > 10:
                                api_key = val
                except Exception:
                    pass

    if not base_url:
        base_url = "https://api.clawdbox.cn"

    return base_url.rstrip("/"), api_key


def generate_image(base_url, api_key, prompt, model, size, n, watermark, extend):
    """调用图片生成 API"""
    body = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size.replace("x", "*"),
        "response_format": "url",
    }
    extra = {}
    if not watermark:
        extra["watermark"] = False
    if not extend:
        extra["prompt_extend"] = False
    if extra:
        body["extra"] = extra

    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        f"{base_url}/v1/images/generations",
        data=data, headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("data", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"API Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def edit_image(base_url, api_key, image, prompt, model, size):
    """调用图片编辑 API"""
    body = {
        "model": model or "qwen-image-edit-plus",
        "image": image,
        "prompt": prompt,
        "n": 1,
        "size": size.replace("x", "*"),
    }
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        f"{base_url}/v1/images/edits",
        data=data, headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("data", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"API Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def download_image(url, dest):
    """下载图片到本地"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)


def build_gallery(out_dir, mapping):
    """生成 HTML 缩略图画廊"""
    html_parts = [
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
        "<title>ClawdBox Image Gallery</title>",
        "<style>",
        "body{font-family:sans-serif;background:#f5f0e8;color:#2d2a23;padding:20px}",
        "h1{color:#d97706}.grid{display:flex;flex-wrap:wrap;gap:16px}",
        ".card{background:#fff;border-radius:12px;overflow:hidden;width:300px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}",
        ".card img{width:100%;display:block}",
        ".card p{padding:8px 12px;font-size:13px;color:#666;margin:0}",
        "</style></head><body>",
        "<h1>🦞 龙虾智盒 AI 画廊</h1><div class=\"grid\">",
    ]
    for prompt, filename in mapping.items():
        html_parts.append(
            f"<div class=\"card\"><img src=\"{filename}\">"
            f"<p>{html_escape(prompt)}</p></div>"
        )
    html_parts.append("</div></body></html>")
    (out_dir / "index.html").write_text("\n".join(html_parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="龙虾智盒 AI 图片生成")
    parser.add_argument("--prompt", type=str, required=True, help="图片描述提示词")
    parser.add_argument("--model", type=str, default="Qwen-Image-2.0", help="模型名称")
    parser.add_argument("--count", type=int, default=1, help="生成数量")
    parser.add_argument("--size", type=str, default="1024x1024", help="图片尺寸 (宽x高)")
    parser.add_argument("--out-dir", type=str, default=None, help="输出目录")
    parser.add_argument("--no-watermark", action="store_true", help="不添加水印")
    parser.add_argument("--no-extend", action="store_true", help="不自动扩展提示词")
    parser.add_argument("--edit", action="store_true", help="图片编辑模式")
    parser.add_argument("--image", type=str, default=None, help="编辑模式的输入图片 (URL 或本地路径)")

    args = parser.parse_args()
    base_url, api_key = get_api_config()
    out_dir = Path(args.out_dir) if args.out_dir else default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("🦞 龙虾智盒 AI 绘画")
    print(f"   模型: {args.model}")
    print(f"   尺寸: {args.size}")
    print(f"   输出: {out_dir}")
    print()

    if args.edit:
        if not args.image:
            print("编辑模式需要 --image 参数", file=sys.stderr)
            sys.exit(1)
        image_input = args.image
        if os.path.isfile(image_input):
            with open(image_input, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                ext = Path(image_input).suffix.lstrip(".")
                image_input = f"data:image/{ext};base64,{b64}"

        print(f"   编辑图片: {args.image}")
        print(f"   指令: {args.prompt}")
        results = edit_image(base_url, api_key, image_input, args.prompt, args.model, args.size)
    else:
        print(f"   提示词: {args.prompt}")
        if args.count > 1:
            print(f"   数量: {args.count}")
        results = generate_image(
            base_url, api_key, args.prompt, args.model,
            args.size, args.count, not args.no_watermark, not args.no_extend,
        )

    if not results:
        print("未生成任何图片", file=sys.stderr)
        sys.exit(1)

    mapping = {}
    for i, item in enumerate(results):
        url = item.get("url", "")
        b64_data = item.get("b64_json", "")

        suffix = f"-{i + 1}" if len(results) > 1 else ""
        filename = f"{slugify(args.prompt)}{suffix}.png"
        dest = out_dir / filename

        if url:
            print(f"   下载 [{i + 1}/{len(results)}] -> {filename}")
            download_image(url, dest)
        elif b64_data:
            print(f"   保存 [{i + 1}/{len(results)}] -> {filename}")
            dest.write_bytes(base64.b64decode(b64_data))

        mapping[args.prompt + (f" ({i + 1})" if len(results) > 1 else "")] = filename

    (out_dir / "prompts.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    build_gallery(out_dir, mapping)

    print()
    print(f"完成！共 {len(results)} 张图片")
    print(f"   画廊: {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
