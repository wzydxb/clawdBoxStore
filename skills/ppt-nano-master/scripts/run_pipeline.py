#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON_BIN = "/root/.openclaw/venvs/ppt/bin/python"
MAX_PAGE_RENDER_RETRIES = 1


def write_state(path: Path, stage: str, status: str, **extra: object) -> None:
    payload = {
        "stage": stage,
        "status": status,
        **extra,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def render_page(slide: dict, slides_dir: Path) -> str:
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

    last_error: str | None = None
    for attempt in range(MAX_PAGE_RENDER_RETRIES + 1):
        try:
            media_stdout = run(cmd)
            return parse_media_path(media_stdout)
        except Exception as exc:
            last_error = str(exc)
            if attempt >= MAX_PAGE_RENDER_RETRIES:
                break
    raise RuntimeError(last_error or "page render failed")


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
    state_path = output_dir / "job_state.json"

    brief_path = output_dir / "deck_brief.json"
    plan_path = output_dir / "slide_plan.json"
    render_path = output_dir / "render_plan.json"
    styles_json = SCRIPT_DIR.parent / "styles" / "styles.json"

    try:
        write_state(state_path, "THEME_EXTRACT", "running", theme=args.theme)
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

        write_state(state_path, "SLIDE_PLAN", "running", brief=str(brief_path))
        run([
            sys.executable,
            str(SCRIPT_DIR / "plan_slides.py"),
            "--brief", str(brief_path),
            "--max-slides", str(args.slides),
            "--output", str(plan_path),
        ])

        write_state(state_path, "COMPONENT_SELECT", "running", plan=str(plan_path))
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
            write_state(
                state_path,
                f"PAGE_RENDER_{slide['index']}",
                "running",
                slide_index=slide["index"],
                page_type=slide.get("page_type"),
                title=slide.get("title"),
            )
            try:
                media_path = render_page(slide, slides_dir)
                slide_images.append(media_path)
                write_state(
                    state_path,
                    f"PAGE_RENDER_{slide['index']}",
                    "done",
                    slide_index=slide["index"],
                    media_path=media_path,
                )
            except Exception as exc:
                write_state(
                    state_path,
                    f"PAGE_RENDER_{slide['index']}",
                    "failed",
                    slide_index=slide["index"],
                    error_code="IMAGE_GEN_FAILED",
                    error_detail=str(exc),
                )
                print(json.dumps({
                    "status": "FAILED_PARTIAL",
                    "failed_stage": f"PAGE_RENDER_{slide['index']}",
                    "error_code": "IMAGE_GEN_FAILED",
                    "error_detail": str(exc),
                }, ensure_ascii=False, indent=2), file=sys.stderr)
                return 1

        write_state(state_path, "ASSEMBLE", "running", slide_count=len(slide_images))
        pptx_stdout = run([
            PYTHON_BIN,
            str(SCRIPT_DIR / "build_pptx.py"),
            "-i",
            *slide_images,
            "-o",
            str(Path(args.output_pptx).resolve()),
        ])
        pptx_path = parse_pptx_path(pptx_stdout)
        write_state(state_path, "DONE", "done", pptx_path=pptx_path, slide_count=len(slide_images))
        print(f"PPTX:{pptx_path}")
        return 0
    except Exception as exc:
        write_state(state_path, "FAILED", "failed", error_code="PIPELINE_FAILED", error_detail=str(exc))
        print(json.dumps({
            "status": "FAILED",
            "failed_stage": "PIPELINE",
            "error_code": "PIPELINE_FAILED",
            "error_detail": str(exc),
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
