import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).with_name("generate_image.py")
SPEC = importlib.util.spec_from_file_location("generate_image", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize(
    ("max_input_dim", "expected"),
    [
        (0, "2K"),
        (1499, "2K"),
        (1500, "2K"),
        (2999, "2K"),
        (3000, "2K"),
    ],
)
def test_auto_detect_resolution_defaults_to_2k(max_input_dim, expected):
    assert MODULE.auto_detect_resolution(max_input_dim) == expected


@pytest.mark.parametrize(
    ("requested_resolution", "max_input_dim", "has_input_images", "expected"),
    [
        (None, 2200, True, ("2K", False)),
        (None, 0, False, ("2K", False)),
        ("2K", 3500, True, ("2K", False)),
        ("3K", 3500, True, ("3K", False)),
    ],
)
def test_choose_output_resolution_table(
    requested_resolution,
    max_input_dim,
    has_input_images,
    expected,
):
    assert (
        MODULE.choose_output_resolution(
            requested_resolution,
            max_input_dim,
            has_input_images,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("width", "height", "expect_resized", "expected_size"),
    [
        (1600, 1599, False, (1600, 1599)),
        (1600, 1600, False, (1600, 1600)),
        (4000, 2000, True, (2262, 1131)),
        (2000, 4000, True, (1131, 2262)),
    ],
)
def test_resize_image_if_needed_table(width, height, expect_resized, expected_size):
    image = MODULE.PILImage.new("RGB", (width, height), (255, 0, 0))

    resized, did_resize = MODULE.resize_image_if_needed(image)

    assert did_resize is expect_resized
    assert resized.size == expected_size
    assert resized.size[0] * resized.size[1] <= MODULE.MAX_INPUT_PIXELS


def test_map_size_uses_aspect_ratio_mapping():
    assert MODULE.map_size("2K", "16:9") == "1536x1024"
    assert MODULE.map_size("2K", "9:16") == "1024x1536"
    assert MODULE.map_size("2K", "1:1") == "1024x1024"


def test_map_size_defaults_to_square_for_unknown_pair():
    assert MODULE.map_size("2K", None) == "1024x1024"
    assert MODULE.map_size("3K", "21:9") == "1024x1024"


def test_resolve_tool_paths_uses_expected_defaults(monkeypatch):
    existing = {
        MODULE.DEFAULT_LOCAL_PYTHON,
        MODULE.DEFAULT_LOCAL_IMAGE_TOOL,
    }

    monkeypatch.setattr(MODULE.Path, "exists", lambda self: str(self) in existing)

    python_bin, tool_script = MODULE.resolve_tool_paths()

    assert python_bin == MODULE.DEFAULT_LOCAL_PYTHON
    assert tool_script == MODULE.DEFAULT_LOCAL_IMAGE_TOOL


def test_resolve_tool_paths_rejects_missing_runtime(monkeypatch):
    monkeypatch.setattr(MODULE.Path, "exists", lambda self: False)

    with pytest.raises(MODULE.ConfigError):
        MODULE.resolve_tool_paths()
