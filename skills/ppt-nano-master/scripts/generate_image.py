#!/usr/bin/env python3
"""
Generate images for PPT pages using the local clawdbox-image-gen tool.

Usage:
    python generate_image.py --prompt "your image description" --filename "output.jpg" [--resolution 2K|3K]

Multi-image editing (up to 14 images):
    python generate_image.py --prompt "combine these images" --filename "output.jpg" -i img1.png -i img2.png
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image as PILImage

MAX_INPUT_IMAGES = 14
MAX_INPUT_PIXELS = 2_560_000
SUPPORTED_OUTPUT_RESOLUTIONS = ["2K", "3K"]
SUPPORTED_ASPECT_RATIOS = [
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "9:16",
    "16:9",
    "21:9",
]
DEFAULT_LOCAL_IMAGE_TOOL = "/root/.openclaw/workspace/skills/clawdbox-image-gen/scripts/gen.py"
DEFAULT_LOCAL_PYTHON = "/root/.openclaw/venvs/ppt/bin/python"
SIZE_MAP = {
    ("2K", "16:9"): "1536x1024",
    ("3K", "16:9"): "1536x1024",
    ("2K", "9:16"): "1024x1536",
    ("3K", "9:16"): "1024x1536",
    ("2K", "1:1"): "1024x1024",
    ("3K", "1:1"): "1024x1024",
}


class ConfigError(RuntimeError):
    """Raised when the local image generation tool is missing or invalid."""


def auto_detect_resolution(max_input_dim: int) -> str:
    return "2K"


def choose_output_resolution(
    requested_resolution: str | None,
    max_input_dim: int,
    has_input_images: bool,
) -> tuple[str, bool]:
    if requested_resolution is not None:
        return requested_resolution, False
    return auto_detect_resolution(max_input_dim), False


def resize_image_if_needed(image: PILImage.Image) -> tuple[PILImage.Image, bool]:
    width, height = image.size
    if width * height <= MAX_INPUT_PIXELS:
        return image, False

    scale = (MAX_INPUT_PIXELS / float(width * height)) ** 0.5
    resized_width = max(1, int(width * scale))
    resized_height = max(1, int(height * scale))

    resized = image.resize((resized_width, resized_height), PILImage.Resampling.LANCZOS)
    return resized, True


def prepare_input_image(image_path: str) -> tuple[str, int]:
    try:
        with PILImage.open(image_path) as image:
            copied = image.copy()
    except Exception as error:
        raise ConfigError(f"Error loading input image '{image_path}': {error}") from error

    processed_image, resized = resize_image_if_needed(copied)
    width, height = processed_image.size
    if resized:
        processed_image.save(image_path)
        print(
            f"Resized input image: {image_path} -> {width}x{height} "
            f"({width * height} pixels)"
        )
    return image_path, max(width, height)


def resolve_tool_paths() -> tuple[str, str]:
    python_bin = DEFAULT_LOCAL_PYTHON
    tool_script = DEFAULT_LOCAL_IMAGE_TOOL
    if not Path(python_bin).exists():
        raise ConfigError(f"Missing local python runtime: {python_bin}")
    if not Path(tool_script).exists():
        raise ConfigError(f"Missing local image tool: {tool_script}")
    return python_bin, tool_script


def map_size(resolution: str, aspect_ratio: str | None) -> str:
    if aspect_ratio is None:
        return "1024x1024"
    return SIZE_MAP.get((resolution, aspect_ratio), "1024x1024")


def run_local_image_tool(
    prompt: str,
    output_path: Path,
    resolution: str,
    aspect_ratio: str | None,
    input_images: list[str] | None,
) -> None:
    python_bin, tool_script = resolve_tool_paths()
    temp_dir = output_path.parent / f".{output_path.stem}-gen"
    temp_dir.mkdir(parents=True, exist_ok=True)

    size = map_size(resolution, aspect_ratio)
    command = [
        python_bin,
        tool_script,
        "--prompt",
        prompt,
        "--size",
        size,
        "--out-dir",
        str(temp_dir),
        "--no-watermark",
    ]

    if input_images:
        command.extend(["--edit", "--image", input_images[0]])

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "local image tool failed")

    png_files = sorted(temp_dir.glob("*.png"))
    if not png_files:
        raise RuntimeError("local image tool produced no image files")

    generated = png_files[0]
    with PILImage.open(generated) as image:
        image.convert("RGB").save(output_path, format="JPEG", quality=95)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate images using the local clawdbox image generation tool"
    )
    parser.add_argument("--prompt", "-p", required=True, help="Image description/prompt")
    parser.add_argument("--filename", "-f", required=True, help="Output filename (e.g., output.jpg)")
    parser.add_argument(
        "--input-image",
        "-i",
        action="append",
        dest="input_images",
        metavar="IMAGE",
        help="Input image path(s) for editing/composition. Can be specified multiple times (up to 14 images).",
    )
    parser.add_argument(
        "--resolution",
        "-r",
        choices=SUPPORTED_OUTPUT_RESOLUTIONS,
        default=None,
        help="Output resolution: 2K or 3K. If omitted, defaults to 2K.",
    )
    parser.add_argument(
        "--aspect-ratio",
        "-a",
        choices=SUPPORTED_ASPECT_RATIOS,
        default=None,
        help=f"Output aspect ratio (default: square). Options: {', '.join(SUPPORTED_ASPECT_RATIOS)}",
    )

    args = parser.parse_args()
    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        max_input_dim = 0
        prepared_inputs: list[str] = []
        if args.input_images:
            if len(args.input_images) > MAX_INPUT_IMAGES:
                print(
                    f"Error: Too many input images ({len(args.input_images)}). Maximum is {MAX_INPUT_IMAGES}.",
                    file=sys.stderr,
                )
                return 1
            for image_path in args.input_images:
                prepared, current_dim = prepare_input_image(image_path)
                prepared_inputs.append(prepared)
                max_input_dim = max(max_input_dim, current_dim)
                print(f"Loaded input image: {image_path}")

        output_resolution, auto_detected = choose_output_resolution(
            requested_resolution=args.resolution,
            max_input_dim=max_input_dim,
            has_input_images=bool(args.input_images),
        )
        if auto_detected:
            print(f"Auto-detected resolution: {output_resolution}")

        if prepared_inputs:
            img_count = len(prepared_inputs)
            print(
                f"Processing {img_count} image{'s' if img_count > 1 else ''} with resolution {output_resolution}..."
            )
        else:
            print(f"Generating image with resolution {output_resolution}...")

        run_local_image_tool(
            prompt=args.prompt,
            output_path=output_path,
            resolution=output_resolution,
            aspect_ratio=args.aspect_ratio,
            input_images=prepared_inputs or None,
        )

        full_path = output_path.resolve()
        print(f"\nImage saved: {full_path}")
        print(f"MEDIA:{full_path}")
        return 0
    except ConfigError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error generating image: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
