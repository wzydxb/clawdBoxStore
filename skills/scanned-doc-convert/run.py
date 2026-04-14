#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_SUBCOMMANDS = {"upload", "convert", "pdf2docx", "ocr2txt", "auto-convert"}


def _resolve_impl_script() -> Path:
    skill_root = Path(__file__).resolve().parent
    impl_script = skill_root / "scripts" / "run_scanned_doc_convert.py"
    if not impl_script.is_file():
        raise FileNotFoundError(f"Missing implementation script: {impl_script}")
    return impl_script.resolve()


def _normalize_argv(argv: list[str]) -> list[str]:
    if len(argv) <= 1:
        return argv

    first_arg = argv[1]
    if first_arg in _SUBCOMMANDS:
        return argv

    remaining = argv[1:]
    if "--input" in remaining and "--output" in remaining:
        return [argv[0], "auto-convert", *remaining]

    if len(remaining) == 2 and not remaining[0].startswith("-") and not remaining[1].startswith("-"):
        return [argv[0], "auto-convert", "--input", remaining[0], "--output", remaining[1]]

    return argv


def main() -> None:
    impl_script = _resolve_impl_script()
    sys.argv = _normalize_argv(list(sys.argv))
    sys.argv[0] = str(impl_script)
    runpy.run_path(str(impl_script), run_name="__main__")


if __name__ == "__main__":
    main()
