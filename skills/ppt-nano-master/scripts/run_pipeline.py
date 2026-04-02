#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON_BIN = "/root/.openclaw/venvs/ppt/bin/python"


def run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {' '.join(args)}")
    return result.stdout.strip()


def parse_media_path(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("MEDIA:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("MEDIA path not found")


def parse_pptx_path(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("PPTX:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("PPTX path not found")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full PPT-Nano pipeline")
    parser.add_argument("--theme", required=True)
    parser.add_argument("--research-text")
    parser.add_argument("--research-file")
    parser.add_argument("--audience", default="管理层")
    parser.add_argument("--slides", type=int, default=8)
    parser.add_argument("--style", default="whiteboard")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-pptx", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    slides_dir = output_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    brief_path = output_dir / "deck_brief.json"
    plan_path = output_dir / "slide_plan.json"
    render_path = output_dir / "render_plan.json"
    styles_json = SCRIPT_DIR.parent / "styles" / "styles.json"

    run([
        sys.executable,
        str(SCRIPT_DIR / "extract_theme.py"),
        "--theme", args.theme,
        "--audience", args.audience,
        "--slides", str(args.slides),
        "--output", str(brief_path),
        *(["--research-text", args.research_text] if args.research_text else []),
        *(["--research-file", args.research_file] if args.research_file else []),
    ])

    run([
        sys.executable,
        str(SCRIPT_DIR / "plan_slides.py"),
        "--brief", str(brief_path),
        "--max-slides", str(args.slides),
        "--output", str(plan_path),
    ])

    run([
        sys.executable,
        str(SCRIPT_DIR / "select_components.py"),
        "--brief", str(brief_path),
        "--plan", str(plan_path),
        "--styles", str(styles_json),
        "--style", args.style,
        "--output", str(render_path),
    ])

    render_plan = json.loads(render_path.read_text(encoding="utf-8"))
    slide_images: list[str] = []
    for slide in render_plan.get("slides", []):
        output_file = slides_dir / f"slide-{slide['index']:02d}.jpg"
        cmd = [
            PYTHON_BIN,
            str(SCRIPT_DIR / "generate_image.py"),
            "--prompt", slide["final_prompt"],
            "--filename", str(output_file),
            "--resolution", "2K",
            "--aspect-ratio", "16:9",
        ]
        if slide.get("reference_image"):
            cmd.extend(["-i", str(SCRIPT_DIR.parent / slide["reference_image"])])
        media_stdout = run(cmd)
        slide_images.append(parse_media_path(media_stdout))

    pptx_stdout = run([
        PYTHON_BIN,
        str(SCRIPT_DIR / "build_pptx.py"),
        "-i",
        *slide_images,
        "-o",
        str(Path(args.output_pptx).resolve()),
    ])
    print(f"PPTX:{parse_pptx_path(pptx_stdout)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
