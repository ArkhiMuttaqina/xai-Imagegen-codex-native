#!/usr/bin/env python3
"""Dependency-free stdio MCP image server for HashMicro XAI."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid


SERVER_NAME = "hashmicro-imagegen-native"
SERVER_VERSION = "0.1.6"
SAFE_SIZES = {"1024x1024", "1536x1024", "1024x1536"}
RATIO_SIZES = {
    "1:1": "1024x1024",
    "9:16": "1024x1536",
    "2:3": "1024x1536",
    "3:4": "1024x1536",
    "16:9": "1536x1024",
    "3:2": "1536x1024",
    "4:3": "1536x1024",
}
VALID_QUALITIES = {"low", "medium", "high"}
_JOBS: dict[str, dict[str, object]] = {}
_JOBS_LOCK = threading.Lock()


class GatewayHTTPError(RuntimeError):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HashMicro XAI HTTP {status_code}: {detail}")


def _load_env() -> None:
    candidates = [Path.cwd() / ".env", Path.home() / ".codex" / ".env"]
    for path in candidates:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                os.environ.setdefault(key, value)


def _base_url() -> str:
    value = os.getenv("XAI_URL", "").rstrip("/")
    if value.endswith("/v1"):
        value = value[:-3].rstrip("/")
    if not value:
        raise RuntimeError("XAI_URL is not configured")
    return value


def _api_key() -> str:
    value = os.getenv("XAI_HASHMICRO_API_KEY", "")
    if not value:
        raise RuntimeError("XAI_HASHMICRO_API_KEY is not configured")
    return value


def _model(value: object) -> str:
    model = ""
    for candidate in (
        value,
        os.getenv("CODEX_REQUEST_MODEL"),
        os.getenv("CODEX_SESSION_MODEL"),
        os.getenv("CODEX_MODEL"),
        os.getenv("XAI_IMAGE_MODEL"),
    ):
        if candidate is not None and str(candidate).strip():
            model = str(candidate).strip()
            break
    if not model:
        raise RuntimeError(
            "No image model is configured. Pass the active Codex model explicitly "
            "or set XAI_IMAGE_MODEL in ~/.codex/.env."
        )
    if model.startswith("codex/") or "/" in model:
        return model
    if model.startswith("gpt-"):
        return "codex/" + model
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)+(?:-[A-Za-z0-9._-]+)?", model):
        return "codex/gpt-" + model
    return model


def _effort(value: object) -> str | None:
    effort = str(value or os.getenv("XAI_REASONING_EFFORT") or "").strip().lower()
    if not effort:
        return None
    if effort == "light":
        effort = "low"
    if effort not in {"low", "medium", "high", "xhigh", "max", "ultra"}:
        raise RuntimeError("Invalid reasoning_effort")
    return effort


def _size_and_prompt(prompt: str, value: object, *, edit: bool) -> tuple[str, str, str | None]:
    requested = str(value or ("1024x1024" if edit else "auto")).strip().lower()
    if requested == "auto" and not edit:
        return "auto", prompt, None
    if requested == "auto" and edit:
        framed_prompt = (
            f"{prompt}\n\nOutput framing requirement: preserve a 1:1 aspect-ratio composition "
            "(square) and keep the main subject crop-safe."
        )
        return "1024x1024", framed_prompt, "auto -> 1024x1024"
    if requested in SAFE_SIZES:
        return requested, prompt, None

    mapped = RATIO_SIZES.get(requested)
    ratio = requested if mapped else None
    if mapped is None:
        match = re.fullmatch(r"([1-9][0-9]*)x([1-9][0-9]*)", requested)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            mapped = "1536x1024" if width > height else "1024x1536" if width < height else "1024x1024"
            ratio = f"{width}:{height}"
    if mapped is None:
        raise RuntimeError(
            "Invalid size. Use auto, a supported pixel size, or an aspect ratio such as 9:16, 16:9, or 1:1."
        )

    left, right = (int(part) for part in ratio.split(":"))
    orientation = "portrait" if left < right else "landscape" if left > right else "square"
    framed_prompt = (
        f"{prompt}\n\nOutput framing requirement: preserve a {ratio} aspect-ratio composition "
        f"({orientation}) and keep the main subject crop-safe."
    )
    return mapped, framed_prompt, f"{requested} -> {mapped}"


def _quality(value: object) -> str:
    quality = str(value or "medium").strip().lower()
    if quality not in VALID_QUALITIES:
        raise RuntimeError("Invalid quality")
    return quality


def _request_timeout_sec() -> int:
    raw = os.getenv("XAI_IMAGE_TIMEOUT_SEC", "600").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 600
    return max(30, min(value, 840))


def _job_ttl_sec() -> int:
    raw = os.getenv("XAI_IMAGE_JOB_TTL_SEC", "3600").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 3600
    return max(300, min(value, 86400))


def _request(url: str, data: bytes, content_type: str) -> dict:
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    timeout_sec = _request_timeout_sec()
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise GatewayHTTPError(exc.code, detail) from exc
    except (TimeoutError, urllib.error.URLError) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            raise RuntimeError(
                f"HashMicro XAI request timed out after {timeout_sec}s. "
                "The upstream request may still have run; do not automatically submit it again."
            ) from exc
        raise RuntimeError(f"Could not reach HashMicro XAI: {reason}") from exc


def _multipart(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = "----codex-" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
            value.encode("utf-8"),
            b"\r\n",
        ])
    for field_name, path in files:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'.encode(),
            f"Content-Type: {mime}\r\n\r\n".encode(),
            path.read_bytes(),
            b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _output_path(raw: object, suffix: str = ".png") -> Path:
    if raw:
        path = Path(str(raw)).expanduser()
    else:
        path = Path.cwd() / "outputs" / f"hashmicro-image-{uuid.uuid4().hex[:8]}{suffix}"
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path = path.with_name(f"{path.stem}-{uuid.uuid4().hex[:6]}{path.suffix}")
    return path.resolve()


def _finish(response: dict, out_path: Path, model: str, size_note: str | None = None) -> list[dict]:
    items = response.get("data") or []
    if not items or not items[0].get("b64_json"):
        raise RuntimeError("Gateway response did not contain data[0].b64_json")
    image_b64 = items[0]["b64_json"]
    raw = base64.b64decode(image_b64)
    out_path.write_bytes(raw)
    mime = "image/png"
    if raw[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif raw[:4] == b"RIFF" and b"WEBP" in raw[:16]:
        mime = "image/webp"
    note = f"Saved: {out_path}\nModel: {model}"
    if size_note:
        note += f"\nSize mapping: {size_note}"
    return [
        {"type": "text", "text": note},
        {"type": "image", "data": image_b64, "mimeType": mime},
    ]


def _generate(args: dict) -> list[dict]:
    model = _model(args.get("model"))
    size, prompt, size_note = _size_and_prompt(str(args["prompt"]), args.get("size"), edit=False)
    payload: dict[str, object] = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": _quality(args.get("quality")),
        "output_format": "png",
    }
    effort = _effort(args.get("reasoning_effort"))
    if effort:
        payload["reasoning_effort"] = effort
    body = json.dumps(payload).encode("utf-8")
    response = _request(f"{_base_url()}/v1/images/generations", body, "application/json")
    return _finish(response, _output_path(args.get("out")), model, size_note)


def _edit_sync(args: dict) -> list[dict]:
    model = _model(args.get("model"))
    size, prompt, size_note = _size_and_prompt(str(args["prompt"]), args.get("size"), edit=True)
    paths = [Path(str(p)).expanduser().resolve() for p in args.get("images", [])]
    if not paths:
        raise RuntimeError("images must contain at least one local path")
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Image not found: {path}")
    fields = {
        "model": model,
        "prompt": prompt,
        "n": "1",
        "size": size,
        "quality": _quality(args.get("quality")),
        "output_format": "png",
    }
    effort = _effort(args.get("reasoning_effort"))
    if effort:
        fields["reasoning_effort"] = effort
    body, content_type = _multipart(fields, [("image", path) for path in paths])
    response = _request(f"{_base_url()}/v1/images/edits", body, content_type)
    return _finish(response, _output_path(args.get("out")), model, size_note)


def _run_edit_job(job_id: str, args: dict) -> None:
    try:
        content = _edit_sync(args)
        with _JOBS_LOCK:
            _JOBS[job_id] = {"status": "completed", "content": content, "updated": time.time()}
    except Exception as exc:
        with _JOBS_LOCK:
            _JOBS[job_id] = {"status": "failed", "error": str(exc), "updated": time.time()}


def _cleanup_jobs() -> None:
    cutoff = time.time() - _job_ttl_sec()
    with _JOBS_LOCK:
        expired = [job_id for job_id, job in _JOBS.items() if float(job.get("updated", 0)) < cutoff]
        for job_id in expired:
            _JOBS.pop(job_id, None)


def _start_edit(args: dict) -> list[dict]:
    # Validate all inexpensive inputs before returning a job id.
    _cleanup_jobs()
    _model(args.get("model"))
    _effort(args.get("reasoning_effort"))
    _size_and_prompt(str(args["prompt"]), args.get("size"), edit=True)
    _quality(args.get("quality"))
    paths = [Path(str(p)).expanduser().resolve() for p in args.get("images", [])]
    if not paths:
        raise RuntimeError("images must contain at least one local path")
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Image not found: {path}")

    job_id = uuid.uuid4().hex
    with _JOBS_LOCK:
        _JOBS[job_id] = {"status": "running", "updated": time.time()}
    worker = threading.Thread(
        target=_run_edit_job,
        args=(job_id, dict(args)),
        name=f"hashmicro-edit-{job_id[:8]}",
        daemon=True,
    )
    worker.start()
    return [{
        "type": "text",
        "text": (
            f"Edit started in background.\nJob: {job_id}\nStatus: running\n"
            "Poll hashmicro_get_image_result with this job id; do not submit the edit again."
        ),
    }]


def _get_image_result(args: dict) -> list[dict]:
    _cleanup_jobs()
    job_id = str(args.get("job_id") or "").strip()
    if not job_id:
        raise RuntimeError("job_id is required")
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        raise RuntimeError(f"Unknown or expired image job: {job_id}")
    status = job.get("status")
    if status == "running":
        return [{
            "type": "text",
            "text": f"Job: {job_id}\nStatus: running\nPoll again later; do not submit the edit again.",
        }]
    if status == "failed":
        raise RuntimeError(f"HashMicro edit job failed: {job.get('error')}")
    content = job.get("content")
    if not isinstance(content, list):
        raise RuntimeError(f"Image job {job_id} completed without a valid result")
    return content


TOOLS = [
    {
        "name": "hashmicro_generate_image",
        "description": "Generate one image through HashMicro XAI and return a native MCP image result plus a saved local path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "out": {"type": "string"},
                "model": {"type": "string"},
                "reasoning_effort": {"type": "string"},
                "size": {"type": "string", "default": "auto", "description": "A supported pixel size or an aspect ratio such as 9:16, 16:9, or 1:1."},
                "quality": {"type": "string", "default": "medium", "enum": ["low", "medium", "high"]},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "hashmicro_edit_image",
        "description": "Start an image edit in the background through HashMicro XAI and promptly return a job id. Poll hashmicro_get_image_result until it returns the native image result.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "images": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "out": {"type": "string"},
                "model": {"type": "string"},
                "reasoning_effort": {"type": "string"},
                "size": {"type": "string", "default": "1024x1024", "description": "A supported pixel size or an aspect ratio such as 9:16, 16:9, or 1:1."},
                "quality": {"type": "string", "default": "medium", "enum": ["low", "medium", "high"]},
            },
            "required": ["prompt", "images"],
        },
    },
    {
        "name": "hashmicro_get_image_result",
        "description": "Poll a background HashMicro image edit job. Returns status while running, or the native image result plus saved path when complete.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
    },
]


def _send(message: dict) -> None:
    raw = json.dumps(message, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(raw + b"\n")
    sys.stdout.buffer.flush()


def _reply(request: dict) -> dict | None:
    request_id = request.get("id")
    method = request.get("method")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            content = (
                _generate(args)
                if name == "hashmicro_generate_image"
                else _start_edit(args)
                if name == "hashmicro_edit_image"
                else _get_image_result(args)
                if name == "hashmicro_get_image_result"
                else None
            )
            if content is None:
                raise RuntimeError(f"Unknown tool: {name}")
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": content, "isError": False}}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": f"Error: {exc}"}], "isError": True},
            }
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}


def main() -> None:
    _load_env()
    stream = sys.stdin.buffer
    for line in stream:
        if not line.strip():
            continue
        request = json.loads(line.decode("utf-8"))
        response = _reply(request)
        if response is not None:
            _send(response)


if __name__ == "__main__":
    main()
