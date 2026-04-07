#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RENDER_PYTHON = os.environ.get('PPT_STUDIO_PYTHON', sys.executable)


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {' '.join(args)}")


def main() -> int:
    parser = argparse.ArgumentParser(description='Run the 3-step ppt-studio pipeline')
    parser.add_argument('--theme', required=True)
    parser.add_argument('--research-text')
    parser.add_argument('--research-file')
    parser.add_argument('--audience', default='管理层')
    parser.add_argument('--slides', type=int, default=6)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    run([
        sys.executable, str(SCRIPT_DIR / 'step1_plan.py'),
        '--theme', args.theme,
        '--audience', args.audience,
        '--slides', str(args.slides),
        '--output-dir', str(out_dir),
        *( ['--research-text', args.research_text] if args.research_text else [] ),
        *( ['--research-file', args.research_file] if args.research_file else [] ),
    ])
    run([
        sys.executable, str(SCRIPT_DIR / 'step2_generate_assets.py'),
        '--plan', str(out_dir / 'deck_plan.json'),
        '--output-dir', str(out_dir),
    ])
    run([
        RENDER_PYTHON, str(SCRIPT_DIR / 'step3_render_pptx.py'),
        '--plan', str(out_dir / 'deck_plan.json'),
        '--specs', str(out_dir / 'slide_specs.json'),
        '--assets', str(out_dir / 'slide_assets_manifest.json'),
        '--style-resolution', str(out_dir / 'style_resolution.json'),
        '--output', str(out_dir / 'presentation.pptx'),
    ])
    print(f"PPTX:{out_dir / 'presentation.pptx'}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
