#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import time
import re
import unicodedata
from pathlib import Path
import argparse
import tempfile
import mimetypes

import requests

DEFAULT_TIMEOUT = 300
DEFAULT_UPLOAD_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_POLL_INTERVAL = 1.0
DEFAULT_MAX_WAIT_TIME = 180.0
DEFAULT_RELEASE_BASE_URL_ENV = "OPENCLAW_RELEASE_BASE_URL"
DEFAULT_PDF_PAGE_MAX_SIDE = 2048

STATUS_SUCCESS = 2
STATUS_FAILED = 3
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}


class ConfigError(RuntimeError):
    """Raised when required OpenClaw configuration is missing or invalid."""


class OpenClawApiClient:
    def __init__(self, base_url: str, auth_uid: str, auth_token: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "x-auth-uid": auth_uid,
                "x-auth-token": auth_token,
            }
        )

    def post(self, path: str, payload: dict) -> dict:
        response = self.session.post(
            f"{self.base_url}{path}",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"接口响应不是 JSON object: {path}")
        return data

    def request_upload_presign(self, payload: dict) -> dict:
        return self.post("/ocr/v1/uploads", payload)

    def submit_general_converter(self, payload: dict) -> dict:
        return self.post("/ocr/v1/general_converter", payload)

    def submit_text_recognition(self, payload: dict) -> dict:
        return self.post("/ocr/v1/text_recognition", payload)

    def query_task(self, operation: str, commit_id: str) -> dict:
        return self.post(
            "/ocr/v1/query",
            {"operation": operation, "commit_id": commit_id},
        )


def resolve_state_dir(home_dir: Path | None = None) -> Path:
    return (home_dir or Path.home()) / ".openclaw"


def load_json_file(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"Missing required file: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"Invalid JSON in file: {path}") from error


def normalize_non_empty_string(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def normalize_base_url(value: str) -> str:
    trimmed = value.strip().rstrip("/")
    if not trimmed:
        raise ConfigError("openclaw baseUrl must be a non-empty string")
    return trimmed


def extract_base_url_from_config(config_data: object) -> str:
    if not isinstance(config_data, dict):
        raise ConfigError("openclaw config must be a JSON object")

    models = config_data.get("models")
    if not isinstance(models, dict):
        raise ConfigError("openclaw config missing models.providers.openclaw.baseUrl")

    providers = models.get("providers")
    if not isinstance(providers, dict):
        raise ConfigError("openclaw config missing models.providers.openclaw.baseUrl")

    openclaw = providers.get("openclaw")
    if not isinstance(openclaw, dict):
        raise ConfigError("openclaw config missing models.providers.openclaw.baseUrl")

    base_url = normalize_non_empty_string(openclaw.get("baseUrl"))
    if not base_url:
        raise ConfigError("openclaw config missing models.providers.openclaw.baseUrl")
    return normalize_base_url(base_url)


def extract_auth_from_userinfo(userinfo_data: object) -> tuple[str, str]:
    if not isinstance(userinfo_data, dict):
        raise ConfigError("openclaw userinfo must be a JSON object")

    uid = normalize_non_empty_string(userinfo_data.get("uid"))
    token = normalize_non_empty_string(userinfo_data.get("token"))
    if not uid or not token:
        raise ConfigError("openclaw userinfo invalid: uid/token must be non-empty strings")
    return uid, token


def load_openclaw_runtime_config(state_dir: Path) -> tuple[str, str, str]:
    config_path = state_dir / "openclaw.json"
    userinfo_path = state_dir / "identity" / "openclaw-userinfo.json"
    base_url = extract_base_url_from_config(load_json_file(config_path))
    uid, token = extract_auth_from_userinfo(load_json_file(userinfo_path))
    return base_url, uid, token


def _ensure_parent(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: dict) -> None:
    _ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON 顶层必须是 object: {path}")
    return data


def _write_text(path: Path, text: str) -> Path:
    _ensure_parent(path)
    path.write_text(text, encoding="utf-8")
    return path


def _download_to_path(url: str, output_path: Path, timeout_sec: int) -> Path:
    response = requests.get(url, timeout=timeout_sec)
    response.raise_for_status()
    _ensure_parent(output_path)
    output_path.write_bytes(response.content)
    return output_path


def _put_file(upload_url: str, input_path: Path, headers: dict[str, str], timeout_sec: int) -> None:
    response = requests.put(
        upload_url,
        data=input_path.read_bytes(),
        headers=headers,
        timeout=timeout_sec,
    )
    response.raise_for_status()


def _infer_source_kind(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in _IMAGE_SUFFIXES:
        return "image"
    if suffix == ".pdf":
        return "pdf"
    raise ValueError(f"仅支持图片或 PDF 输入: {file_path}")


def _is_image_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in _IMAGE_SUFFIXES


def _infer_upload_file_type(file_path: Path) -> str:
    return "image" if _infer_source_kind(file_path) == "image" else "pdf"


def _resolve_content_type(input_path: Path, file_type: str) -> str:
    if file_type == "pdf":
        return "application/pdf"
    guessed, _ = mimetypes.guess_type(str(input_path))
    return guessed or "application/octet-stream"


def _ensure_upload_size_within_limit(input_path: Path) -> None:
    max_bytes = int(os.environ.get("AGILEOCR_UPLOAD_MAX_BYTES", str(DEFAULT_UPLOAD_MAX_BYTES)))
    if input_path.stat().st_size > max_bytes:
        raise ValueError(f"上传文件大小不能超过 {max_bytes} 字节: {input_path}")


def _extract_commit_id(response: dict) -> str:
    commit_id = str(response.get("commit_id", "")).strip()
    if not commit_id:
        raise RuntimeError(f"接口响应缺少 commit_id: {response}")
    return commit_id


def _extract_status(response: dict) -> int | None:
    status = response.get("status")
    if isinstance(status, int):
        return status
    if isinstance(status, str) and status.strip().isdigit():
        return int(status.strip())
    return None


def _extract_payload(response: dict) -> dict:
    payload = response.get("payload")
    if not isinstance(payload, dict):
        raise RuntimeError(f"接口响应缺少 payload: {response}")
    return payload


def _wait_for_terminal_result(
    client: OpenClawApiClient,
    *,
    operation: str,
    commit_id: str,
    poll_interval: float,
    max_wait_time: float,
) -> dict:
    start = time.time()
    while True:
        if time.time() - start > max_wait_time:
            raise TimeoutError(f"等待任务超时: operation={operation}, commit_id={commit_id}")
        result = client.query_task(operation, commit_id)
        status = _extract_status(result)
        if status == STATUS_SUCCESS:
            return result
        if status == STATUS_FAILED:
            raise RuntimeError(f"任务失败: {result}")
        time.sleep(poll_interval)


def _normalize_upload_meta(response: dict) -> dict:
    payload = _extract_payload(response)
    normalized = dict(payload)
    normalized["_backend"] = {
        "commit_id": _extract_commit_id(response),
        "status": _extract_status(response),
    }
    return normalized


def _resolve_upload_meta(
    client: OpenClawApiClient,
    submit_response: dict,
    *,
    poll_interval: float,
    max_wait_time: float,
) -> dict:
    upload_meta = _normalize_upload_meta(submit_response)
    if str(upload_meta.get("upload_url", "")).strip():
        return upload_meta
    terminal = _wait_for_terminal_result(
        client,
        operation="uploads_presign",
        commit_id=_extract_commit_id(submit_response),
        poll_interval=poll_interval,
        max_wait_time=max_wait_time,
    )
    return _normalize_upload_meta(terminal)


def _extract_upload_source(upload_meta_path: Path) -> tuple[str, str]:
    meta = _load_json(upload_meta_path)
    source_url = str(meta.get("source_url", "")).strip()
    if not source_url:
        raise ValueError(f"上传结果缺少 source_url: {meta}")
    filename = str(meta.get("filename", "")).strip() or Path(source_url).name
    return source_url, filename


def _infer_convert_task(upload_meta_path: Path) -> tuple[str, str, str]:
    source_url, filename = _extract_upload_source(upload_meta_path)
    task, _ = _infer_convert_task_by_filename(filename)
    return source_url, filename, task


def _infer_convert_task_by_filename(filename: str) -> tuple[str, str]:
    if _infer_source_kind(Path(filename)) == "pdf":
        return "imgpdf_2_pdf", "imgpdf"
    return "image_2_pdf", "image"


def _submit_converter_and_download(
    client: OpenClawApiClient,
    *,
    task: str,
    media_type: str,
    filename: str,
    source_url: str,
    poll_interval: float,
    max_wait_time: float,
    timeout_sec: int,
    output_path: Path,
) -> Path:
    submit_result = client.submit_general_converter(
        {
            "task": task,
            "media_type": media_type,
            "filename": filename,
            "source_url": source_url,
            "persist": False,
            "extras": {},
        }
    )
    terminal = _wait_for_terminal_result(
        client,
        operation="general_converter",
        commit_id=_extract_commit_id(submit_result),
        poll_interval=poll_interval,
        max_wait_time=max_wait_time,
    )
    result_payload = _extract_payload(terminal)
    download_url = str(result_payload.get("download_url", "")).strip()
    if not download_url:
        raise RuntimeError(f"{task} 结果缺少 download_url: {terminal}")
    return _download_to_path(download_url, output_path, timeout_sec)


def _convert_input_file_to_pdf(
    client: OpenClawApiClient,
    *,
    input_path: Path,
    output_path: Path,
    poll_interval: float,
    max_wait_time: float,
    timeout_sec: int,
) -> Path:
    if input_path.is_dir():
        raise ValueError(f"convert 仅支持单个图片或 PDF 文件输入: {input_path}")
    _infer_source_kind(input_path)
    upload_meta = _upload_file_via_api(client, input_path, timeout_sec)
    source_url = str(upload_meta.get("source_url", "")).strip()
    if not source_url:
        raise RuntimeError(f"上传结果缺少 source_url: {upload_meta}")
    task, media_type = _infer_convert_task_by_filename(input_path.name)
    return _submit_converter_and_download(
        client,
        task=task,
        media_type=media_type,
        filename=input_path.name,
        source_url=source_url,
        poll_interval=poll_interval,
        max_wait_time=max_wait_time,
        timeout_sec=timeout_sec,
        output_path=output_path,
    )


def _convert_pdf_file_to_docx(
    client: OpenClawApiClient,
    *,
    input_path: Path,
    output_path: Path,
    poll_interval: float,
    max_wait_time: float,
    timeout_sec: int,
) -> Path:
    if _infer_source_kind(input_path) != "pdf":
        raise ValueError(f"pdf2docx 仅支持 PDF 输入: {input_path}")
    upload_meta = _upload_file_via_api(client, input_path, timeout_sec)
    source_url = str(upload_meta.get("source_url", "")).strip()
    if not source_url:
        raise RuntimeError(f"pdf2docx 上传结果缺少 source_url: {upload_meta}")
    return _submit_converter_and_download(
        client,
        task="pdf_2_docx",
        media_type="pdf",
        filename=input_path.name,
        source_url=source_url,
        poll_interval=poll_interval,
        max_wait_time=max_wait_time,
        timeout_sec=timeout_sec,
        output_path=output_path,
    )


def _resolve_auto_convert_mode(output_path: Path) -> str:
    suffix = output_path.suffix.lower()
    if suffix not in {".txt", ".pdf", ".docx"}:
        raise ValueError(f"auto-convert 仅支持 .txt / .pdf / .docx 输出: {output_path}")
    return suffix


def _resolve_auth(args: argparse.Namespace) -> tuple[str, str, str]:
    runtime_base_url = ""
    runtime_uid = ""
    runtime_token = ""
    try:
        runtime_base_url, runtime_uid, runtime_token = load_openclaw_runtime_config(
            resolve_state_dir() if args.state_dir is None else Path(args.state_dir).expanduser().resolve()
        )
    except ConfigError:
        pass

    base_url = args.base_url or os.environ.get(DEFAULT_RELEASE_BASE_URL_ENV, "") or runtime_base_url
    auth_uid = args.auth_uid or runtime_uid
    auth_token = args.auth_token or runtime_token
    if not base_url:
        raise ConfigError(
            f"缺少 backend baseUrl，请通过 --base-url、环境变量 {DEFAULT_RELEASE_BASE_URL_ENV} 或 ~/.openclaw/openclaw.json 提供"
        )
    if not auth_uid or not auth_token:
        raise ConfigError("缺少 OpenClaw 鉴权信息，请通过 --auth-uid/--auth-token 或 ~/.openclaw/identity 提供")
    return normalize_base_url(base_url), auth_uid, auth_token


def _make_client(args: argparse.Namespace) -> OpenClawApiClient:
    base_url, auth_uid, auth_token = _resolve_auth(args)
    return OpenClawApiClient(base_url=base_url, auth_uid=auth_uid, auth_token=auth_token, timeout=args.timeout)


def _upload_file_via_api(
    client: OpenClawApiClient,
    input_path: Path,
    timeout_sec: int,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_wait_time: float = DEFAULT_MAX_WAIT_TIME,
) -> dict:
    _ensure_upload_size_within_limit(input_path)
    file_type = _infer_upload_file_type(input_path)
    payload = {
        "file_type": file_type,
        "filename": input_path.name,
        "content_type": _resolve_content_type(input_path, file_type),
    }
    submit_response = client.request_upload_presign(payload)
    upload_meta = _resolve_upload_meta(
        client,
        submit_response,
        poll_interval=poll_interval,
        max_wait_time=max_wait_time,
    )
    upload_url = str(upload_meta.get("upload_url", "")).strip()
    if not upload_url:
        raise RuntimeError(f"上传预签名结果缺少 upload_url: {submit_response}")
    response_headers = upload_meta.get("headers")
    if not isinstance(response_headers, dict):
        raise RuntimeError(f"上传预签名结果缺少 headers: {submit_response}")
    normalized_headers = {str(key): str(value) for key, value in response_headers.items()}
    _put_file(upload_url, input_path, normalized_headers, timeout_sec)
    return upload_meta


def _submit_text_recognition(client: OpenClawApiClient, *, source_url: str, filename: str, poll_interval: float, max_wait_time: float) -> dict:
    submit_result = client.submit_text_recognition(
        {
            "filename": filename,
            "source_url": source_url,
        }
    )
    terminal = _wait_for_terminal_result(
        client,
        operation="text_recognition",
        commit_id=_extract_commit_id(submit_result),
        poll_interval=poll_interval,
        max_wait_time=max_wait_time,
    )
    return _extract_payload(terminal)


def _bbox_metrics(item: dict) -> tuple[float, float, float, float]:
    bbox = item.get("bbox")
    if not isinstance(bbox, list) or len(bbox) < 8:
        return 0.0, 0.0, 0.0, 0.0
    xs = [float(bbox[i]) for i in range(0, 8, 2)]
    ys = [float(bbox[i]) for i in range(1, 8, 2)]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def _extract_text_items(payload: dict) -> list[dict]:
    items = payload.get("text_recognition")
    if not isinstance(items, list):
        raise RuntimeError(f"text_recognition 响应缺少结果数组: {payload}")
    extracted: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if not isinstance(text, dict):
            continue
        value = str(text.get("value", "")).strip()
        if not value:
            continue
        x, y, w, h = _bbox_metrics(item)
        center_y = y + (h / 2.0 if h > 0 else 0.0)
        extracted.append(
            {
                "text": value,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "center_y": center_y,
            }
        )
    return extracted


def _contains_url_like_text(text: str) -> bool:
    lowered = text.lower()
    return "http" in lowered or "www." in lowered or ".com" in lowered or ".cn" in lowered


def _contains_date_like_text(text: str) -> bool:
    return re.search(r"\d{4}年|\d{1,2}月\d{1,2}日", text) is not None


def _line_threshold_by_items(items: list[dict]) -> float:
    heights = [item["height"] for item in items if item["height"] > 0]
    if not heights:
        return 12.0
    median_height = sorted(heights)[len(heights) // 2]
    return min(max(median_height * 0.6, 8.0), 36.0)


def _cluster_text_lines(items: list[dict]) -> list[dict]:
    if not items:
        return []
    line_threshold = _line_threshold_by_items(items)
    sorted_items = sorted(items, key=lambda item: (item["y"], item["x"]))
    lines: list[dict] = []
    for item in sorted_items:
        target_line = None
        for line in lines:
            if abs(item["center_y"] - line["center_y"]) <= line_threshold:
                target_line = line
                break
        if target_line is None:
            lines.append(
                {
                    "y": item["y"],
                    "center_y": item["center_y"],
                    "height": item["height"],
                    "items": [item],
                }
            )
            continue
        target_line["items"].append(item)
        target_line["y"] = min(target_line["y"], item["y"])
        target_line["center_y"] = (target_line["center_y"] + item["center_y"]) / 2.0
        target_line["height"] = max(target_line["height"], item["height"])
    return sorted(lines, key=lambda line: line["y"])


def _transform_items_for_rotation(items: list[dict], direction: str) -> list[dict]:
    if direction not in {"cw", "ccw"}:
        raise ValueError(f"不支持的旋转方向: {direction}")
    max_x = max(item["x"] + item["width"] for item in items)
    max_y = max(item["y"] + item["height"] for item in items)
    transformed: list[dict] = []
    for item in items:
        x0 = item["x"]
        y0 = item["y"]
        x1 = item["x"] + item["width"]
        y1 = item["y"] + item["height"]
        if direction == "cw":
            nx0 = y0
            ny0 = max_x - x1
            nx1 = y1
            ny1 = max_x - x0
        else:
            nx0 = max_y - y1
            ny0 = x0
            nx1 = max_y - y0
            ny1 = x1
        width = max(nx1 - nx0, 0.0)
        height = max(ny1 - ny0, 0.0)
        transformed.append(
            {
                "text": item["text"],
                "x": nx0,
                "y": ny0,
                "width": width,
                "height": height,
                "center_y": ny0 + (height / 2.0 if height > 0 else 0.0),
            }
        )
    return transformed


def _render_lines_from_clustered_lines(lines: list[dict]) -> list[str]:
    def display_width(text: str) -> int:
        width = 0
        for char in text:
            if char == "\t":
                width += 4
                continue
            width += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
        return width

    def estimate_char_unit(clustered_lines: list[dict]) -> float:
        candidates: list[float] = []
        for line in clustered_lines:
            for part in line["items"]:
                part_width = float(part.get("width", 0.0))
                text_width = display_width(str(part.get("text", "")))
                if part_width <= 0 or text_width <= 0:
                    continue
                unit = part_width / float(text_width)
                if 2.0 <= unit <= 60.0:
                    candidates.append(unit)
        if candidates:
            candidates.sort()
            return candidates[len(candidates) // 2]
        line_heights = [float(line.get("height", 0.0)) for line in clustered_lines if float(line.get("height", 0.0)) > 0]
        if line_heights:
            line_heights.sort()
            return max(line_heights[len(line_heights) // 2] * 0.9, 8.0)
        return 12.0

    if not lines:
        return []

    min_x = min(part["x"] for line in lines for part in line["items"])
    char_unit = estimate_char_unit(lines)
    line_heights = [float(line.get("height", 0.0)) for line in lines if float(line.get("height", 0.0)) > 0]
    line_height_ref = sorted(line_heights)[len(line_heights) // 2] if line_heights else 16.0

    rendered: list[str] = []
    previous = None
    for line in lines:
        if previous is not None:
            gap = line["y"] - previous["y"]
            blank_lines = max(int(round(gap / max(line_height_ref, 1.0))) - 1, 0)
            for _ in range(min(blank_lines, 3)):
                rendered.append("")

        line_text_parts: list[str] = []
        current_col = 0
        for part in sorted(line["items"], key=lambda part: part["x"]):
            target_col = int(round((part["x"] - min_x) / max(char_unit, 1.0)))
            target_col = max(0, min(target_col, 240))
            if target_col > current_col:
                spaces = target_col - current_col
            else:
                spaces = 1 if current_col > 0 else 0
            if spaces > 0:
                line_text_parts.append(" " * spaces)
                current_col += spaces
            text = part["text"]
            line_text_parts.append(text)
            current_col += display_width(text)

        rendered_line = "".join(line_text_parts).rstrip()
        if rendered_line:
            rendered.append(rendered_line)
        previous = line
    return rendered


def _score_rendered_lines(lines: list[str]) -> float:
    if not lines:
        return -1e9
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return -1e9
    normalized = [" ".join(line.split()) for line in non_empty]
    top_count = max(3, len(non_empty) // 5)
    top_lines = normalized[:top_count]
    long_line_penalty = sum(max(len(line) - 96, 0) for line in normalized) * 0.05
    top_url_penalty = sum(1 for line in top_lines if _contains_url_like_text(line)) * 3.0
    top_date_penalty = sum(1 for line in top_lines if _contains_date_like_text(line)) * 1.5
    top_footer_penalty = sum(1 for line in top_lines if "监制" in line or "网址" in line) * 2.5
    title_reward = sum(1 for line in top_lines if 3 <= len(line) <= 16 and line.count(" ") <= 2) * 0.8
    return title_reward - long_line_penalty - top_url_penalty - top_date_penalty - top_footer_penalty


def _render_candidate(items: list[dict]) -> list[str]:
    return _render_lines_from_clustered_lines(_cluster_text_lines(items))


def _render_best_text_lines(items: list[dict]) -> list[str]:
    base_lines = _render_candidate(items)
    if not items:
        return base_lines
    vertical_like_count = sum(
        1 for item in items if item["height"] > item["width"] * 1.5 and item["height"] > 0 and item["width"] > 0
    )
    if vertical_like_count / len(items) < 0.7:
        return base_lines
    cw_lines = _render_candidate(_transform_items_for_rotation(items, "cw"))
    ccw_lines = _render_candidate(_transform_items_for_rotation(items, "ccw"))
    candidates = [
        (base_lines, _score_rendered_lines(base_lines)),
        (cw_lines, _score_rendered_lines(cw_lines)),
        (ccw_lines, _score_rendered_lines(ccw_lines)),
    ]
    best_lines, _ = max(candidates, key=lambda item: item[1])
    return best_lines


def _render_text_content(payload: dict) -> str:
    text_items = _extract_text_items(payload)
    return "\n".join(_render_best_text_lines(text_items)).strip()


def _render_pdf_pages_to_images(pdf_path: Path, workspace: Path, max_side_threshold: int) -> list[dict]:
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("处理 PDF 输入需要安装 PyMuPDF") from error

    images: list[dict] = []
    workspace.mkdir(parents=True, exist_ok=True)
    with fitz.open(stream=pdf_path.read_bytes(), filetype="pdf") as pdf_doc:
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            max_side = max(page.rect.width, page.rect.height)
            scale_factor = max_side_threshold / max_side if max_side > 0 else 1.0
            if scale_factor <= 0:
                scale_factor = 1.0
            pix = page.get_pixmap(matrix=fitz.Matrix(scale_factor, scale_factor), alpha=False)
            output_path = workspace / f"page_{page_num + 1}.png"
            output_path.write_bytes(pix.tobytes("png"))
            images.append({"page_num": page_num + 1, "image_path": output_path})
    return images


def _resolve_txt_output_for_directory(output_path: Path) -> Path:
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _resolve_txt_filename(input_path: Path) -> str:
    return f"{input_path.stem}.txt"


def run_upload(args: argparse.Namespace) -> Path:
    input_path = Path(args.input).expanduser().resolve()
    client = _make_client(args)
    upload_meta = _upload_file_via_api(
        client,
        input_path,
        args.timeout,
        poll_interval=args.poll_interval,
        max_wait_time=args.max_wait_time,
    )
    output_path = Path(args.output).expanduser().resolve()
    _write_json(output_path, upload_meta)
    return output_path


def run_convert(args: argparse.Namespace) -> Path:
    upload_meta_path = Path(args.upload_meta).expanduser().resolve()
    source_url, filename, task = _infer_convert_task(upload_meta_path)
    _, media_type = _infer_convert_task_by_filename(filename)
    client = _make_client(args)
    output_path = Path(args.output).expanduser().resolve()
    return _submit_converter_and_download(
        client,
        task=task,
        media_type=media_type,
        filename=filename,
        source_url=source_url,
        poll_interval=args.poll_interval,
        max_wait_time=args.max_wait_time,
        timeout_sec=args.timeout,
        output_path=output_path,
    )


def run_pdf2docx(args: argparse.Namespace) -> Path:
    input_path = Path(args.input).expanduser().resolve()
    client = _make_client(args)
    output_path = Path(args.output).expanduser().resolve()
    return _convert_pdf_file_to_docx(
        client,
        input_path=input_path,
        output_path=output_path,
        poll_interval=args.poll_interval,
        max_wait_time=args.max_wait_time,
        timeout_sec=args.timeout,
    )


def _ocr_single_image_to_txt(client: OpenClawApiClient, image_path: Path, output_path: Path, args: argparse.Namespace) -> Path:
    upload_meta = _upload_file_via_api(
        client,
        image_path,
        args.timeout,
        poll_interval=args.poll_interval,
        max_wait_time=args.max_wait_time,
    )
    source_url = str(upload_meta.get("source_url", "")).strip()
    if not source_url:
        raise RuntimeError(f"上传结果缺少 source_url: {upload_meta}")
    payload = _submit_text_recognition(
        client,
        source_url=source_url,
        filename=image_path.name,
        poll_interval=args.poll_interval,
        max_wait_time=args.max_wait_time,
    )
    return _write_text(output_path, _render_text_content(payload) + "\n")


def run_ocr2txt(args: argparse.Namespace) -> Path:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    client = _make_client(args)

    if input_path.is_dir():
        image_files = sorted(
            path for path in input_path.iterdir() if path.is_file() and _is_image_file(path)
        )
        if not image_files:
            raise ValueError(f"目录中没有可处理的图片文件: {input_path}")
        output_dir = _resolve_txt_output_for_directory(output_path)
        for image_path in image_files:
            txt_path = output_dir / _resolve_txt_filename(image_path)
            _ocr_single_image_to_txt(client, image_path, txt_path, args)
        return output_dir

    if _infer_source_kind(input_path) == "image":
        return _ocr_single_image_to_txt(client, input_path, output_path, args)

    with tempfile.TemporaryDirectory(prefix="scanned-doc-txt-") as temp_dir:
        page_dir = Path(temp_dir) / "pages"
        page_infos = _render_pdf_pages_to_images(input_path, page_dir, args.pdf_page_max_side)
        if not page_infos:
            raise RuntimeError(f"PDF 拆页失败: {input_path}")
        page_texts: list[str] = []
        for page_info in page_infos:
            image_path = Path(page_info["image_path"])
            upload_meta = _upload_file_via_api(
                client,
                image_path,
                args.timeout,
                poll_interval=args.poll_interval,
                max_wait_time=args.max_wait_time,
            )
            source_url = str(upload_meta.get("source_url", "")).strip()
            if not source_url:
                raise RuntimeError(f"上传结果缺少 source_url: {upload_meta}")
            payload = _submit_text_recognition(
                client,
                source_url=source_url,
                filename=image_path.name,
                poll_interval=args.poll_interval,
                max_wait_time=args.max_wait_time,
            )
            content = _render_text_content(payload)
            page_texts.append(
                f"===== 第 {page_info['page_num']} 页 =====\n{content}".rstrip()
            )
        return _write_text(output_path, "\n\n".join(page_texts).strip() + "\n")


def run_auto_convert(args: argparse.Namespace) -> Path:
    output_path = Path(args.output).expanduser().resolve()
    mode = _resolve_auto_convert_mode(output_path)
    if mode == ".txt":
        return run_ocr2txt(args)

    input_path = Path(args.input).expanduser().resolve()
    client = _make_client(args)
    if mode == ".pdf":
        return _convert_input_file_to_pdf(
            client,
            input_path=input_path,
            output_path=output_path,
            poll_interval=args.poll_interval,
            max_wait_time=args.max_wait_time,
            timeout_sec=args.timeout,
        )

    with tempfile.TemporaryDirectory(prefix="scanned-doc-auto-") as temp_dir:
        temp_pdf = Path(temp_dir) / "auto_convert_intermediate.pdf"
        _convert_input_file_to_pdf(
            client,
            input_path=input_path,
            output_path=temp_pdf,
            poll_interval=args.poll_interval,
            max_wait_time=args.max_wait_time,
            timeout_sec=args.timeout,
        )
        return _convert_pdf_file_to_docx(
            client,
            input_path=temp_pdf,
            output_path=output_path,
            poll_interval=args.poll_interval,
            max_wait_time=args.max_wait_time,
            timeout_sec=args.timeout,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenClaw API 版扫描件转换脚本：upload / convert / pdf2docx / ocr2txt / auto-convert"
    )
    parser.add_argument(
        "--base-url",
        default="",
        help=f"OpenClaw backend 地址，默认优先读取环境变量 {DEFAULT_RELEASE_BASE_URL_ENV}，其次读取 ~/.openclaw",
    )
    parser.add_argument("--auth-uid", default="", help="OpenClaw x-auth-uid，默认读取 ~/.openclaw")
    parser.add_argument("--auth-token", default="", help="OpenClaw x-auth-token，默认读取 ~/.openclaw")
    parser.add_argument("--state-dir", default="", help="OpenClaw 本地状态目录，默认 ~/.openclaw")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="请求超时时间（秒），默认 300")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="query 轮询间隔秒数")
    parser.add_argument("--max-wait-time", type=float, default=DEFAULT_MAX_WAIT_TIME, help="query 最大等待秒数")

    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser("upload", help="调用 /ocr/v1/uploads 申请预签名并上传文件")
    upload_parser.add_argument("--input", required=True, help="原始输入文件路径")
    upload_parser.add_argument("--output", required=True, help="输出上传结果 JSON")
    upload_parser.set_defaults(func=run_upload)

    convert_parser = subparsers.add_parser("convert", help="调用 /ocr/v1/general_converter 生成可编辑 PDF")
    convert_parser.add_argument("--upload-meta", required=True, help="upload 结果 JSON")
    convert_parser.add_argument("--output", required=True, help="输出可编辑 PDF")
    convert_parser.set_defaults(func=run_convert)

    pdf2docx_parser = subparsers.add_parser("pdf2docx", help="调用 /ocr/v1/general_converter 生成 DOCX")
    pdf2docx_parser.add_argument("--input", required=True, help="可编辑 PDF 路径")
    pdf2docx_parser.add_argument("--output", required=True, help="输出 DOCX")
    pdf2docx_parser.set_defaults(func=run_pdf2docx)

    ocr2txt_parser = subparsers.add_parser(
        "ocr2txt",
        help="调用 /ocr/v1/text_recognition 将扫描 PDF、单图或图片目录转换为 txt",
    )
    ocr2txt_parser.add_argument("--input", required=True, help="输入文件或图片目录")
    ocr2txt_parser.add_argument("--output", required=True, help="输出 txt 文件或输出目录")
    ocr2txt_parser.add_argument(
        "--pdf-page-max-side",
        type=int,
        default=DEFAULT_PDF_PAGE_MAX_SIDE,
        help="PDF 拆页渲染后页面最大边长度，默认 2048",
    )
    ocr2txt_parser.set_defaults(func=run_ocr2txt)

    auto_convert_parser = subparsers.add_parser(
        "auto-convert",
        help="根据 --output 后缀自动执行 ocr2txt 或 converter 链路",
    )
    auto_convert_parser.add_argument("--input", required=True, help="输入文件或图片目录")
    auto_convert_parser.add_argument("--output", required=True, help="输出目标（.txt / .pdf / .docx）")
    auto_convert_parser.add_argument(
        "--pdf-page-max-side",
        type=int,
        default=DEFAULT_PDF_PAGE_MAX_SIDE,
        help="当输出 .txt 且输入为 PDF 时，拆页渲染后页面最大边长度，默认 2048",
    )
    auto_convert_parser.set_defaults(func=run_auto_convert)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.state_dir == "":
        args.state_dir = None
    output_path = Path(args.func(args)).resolve()
    print(f"[scanned-doc-convert-openclaw-release] 完成: {output_path}")


if __name__ == "__main__":
    main()
