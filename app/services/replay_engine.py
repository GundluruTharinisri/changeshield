import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings


@dataclass
class TrafficRequest:
    method: str
    path: str
    expected_status: int
    headers: dict[str, str]
    body: Any = None


@dataclass
class ReplayResultData:
    method: str
    path: str
    expected_status: int
    actual_status: int | None
    response_time_ms: float
    passed: bool
    error_message: str | None = None


class ReplayInputError(ValueError):
    pass


def validate_candidate_url(candidate_url: str) -> str:
    parsed = urlparse(candidate_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ReplayInputError("candidate_url must be a valid HTTP or HTTPS URL")
    if parsed.username or parsed.password:
        raise ReplayInputError("candidate_url must not contain credentials")
    return candidate_url.rstrip("/")


def parse_traffic(raw: bytes) -> list[TrafficRequest]:
    if len(raw) > settings.max_upload_bytes:
        raise ReplayInputError("Traffic file is too large")
    requests: list[TrafficRequest] = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReplayInputError(f"Invalid JSON on traffic line {line_number}") from exc
        if not isinstance(item, dict):
            raise ReplayInputError(f"Traffic line {line_number} must be a JSON object")
        method = str(item.get("method", "")).upper()
        path = item.get("path")
        expected_status = item.get("expected_status")
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
            raise ReplayInputError(f"Unsupported method on traffic line {line_number}")
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
            raise ReplayInputError(f"Path on traffic line {line_number} must start with a single '/'")
        if not isinstance(expected_status, int) or not 100 <= expected_status <= 599:
            raise ReplayInputError(f"expected_status on traffic line {line_number} must be an HTTP status")
        headers = item.get("headers", {})
        if not isinstance(headers, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()):
            raise ReplayInputError(f"Headers on traffic line {line_number} must be a string map")
        requests.append(TrafficRequest(method, path, expected_status, headers, item.get("body")))
        if len(requests) > settings.max_replay_requests:
            raise ReplayInputError(f"A replay cannot contain more than {settings.max_replay_requests} requests")
    if not requests:
        raise ReplayInputError("Traffic file must contain at least one request")
    return requests


async def replay_traffic(candidate_url: str, traffic: list[TrafficRequest]) -> list[ReplayResultData]:
    base_url = validate_candidate_url(candidate_url)
    results: list[ReplayResultData] = []
    async with httpx.AsyncClient(timeout=settings.replay_timeout_seconds, follow_redirects=False) as client:
        for request in traffic:
            started = time.perf_counter()
            try:
                response = await client.request(
                    request.method,
                    f"{base_url}{request.path}",
                    headers=request.headers,
                    json=request.body if request.body is not None else None,
                )
                elapsed = round((time.perf_counter() - started) * 1000, 2)
                passed = response.status_code == request.expected_status
                results.append(ReplayResultData(
                    request.method,
                    request.path,
                    request.expected_status,
                    response.status_code,
                    elapsed,
                    passed,
                    None if passed else f"Expected {request.expected_status} but received {response.status_code}",
                ))
            except httpx.RequestError as exc:
                elapsed = round((time.perf_counter() - started) * 1000, 2)
                results.append(ReplayResultData(request.method, request.path, request.expected_status, None, elapsed, False, type(exc).__name__))
    return results
