from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
import tomllib

from utils.request_formatter import format_response_request


@dataclass(frozen=True)
class _ProxyConfig:
    upstream_base_url: str
    chat_completions_path: str
    request_timeout_seconds: float


_CONFIG: _ProxyConfig | None = None


def _load_config() -> _ProxyConfig:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    project_root = Path(__file__).resolve().parents[2]
    project_toml_path = project_root / "project.toml"
    data: dict[str, Any] = {}
    if project_toml_path.exists():
        data = tomllib.loads(project_toml_path.read_text(encoding="utf-8"))

    llm_proxy_cfg = data.get("llm_proxy") if isinstance(data, dict) else None
    if not isinstance(llm_proxy_cfg, dict):
        llm_proxy_cfg = {}

    upstream_base_url = llm_proxy_cfg.get("upstream_base_url", "http://localhost:8001")
    chat_completions_path = llm_proxy_cfg.get("chat_completions_path", "/chat/completions")
    timeout = llm_proxy_cfg.get("request_timeout_seconds", 30)

    if not isinstance(upstream_base_url, str) or not upstream_base_url:
        raise ValueError("Invalid config: llm_proxy.upstream_base_url must be a non-empty string")
    if not isinstance(chat_completions_path, str) or not chat_completions_path:
        raise ValueError(
            "Invalid config: llm_proxy.chat_completions_path must be a non-empty string"
        )
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("Invalid config: llm_proxy.request_timeout_seconds must be > 0")

    _CONFIG = _ProxyConfig(
        upstream_base_url=upstream_base_url,
        chat_completions_path=chat_completions_path,
        request_timeout_seconds=float(timeout),
    )
    return _CONFIG


def _build_chat_completions_url(cfg: _ProxyConfig) -> str:
    return cfg.upstream_base_url.rstrip("/") + "/" + cfg.chat_completions_path.lstrip("/")


async def proxy_response(*, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Proxy a public `/response` payload to an upstream `/chat/completions`.
    """

    cfg = _load_config()
    url = _build_chat_completions_url(cfg)

    chat_payload = format_response_request(response_payload=response_payload)

    async with httpx.AsyncClient(timeout=cfg.request_timeout_seconds) as client:
        resp = await client.post(url, json=chat_payload)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("Upstream response must be a JSON object")
        return data


async def proxy_response_stream(*, response_payload: dict[str, Any]) -> AsyncIterator[bytes]:
    """Stream a public `/response` payload to an upstream `/chat/completions`."""

    cfg = _load_config()
    url = _build_chat_completions_url(cfg)

    chat_payload = format_response_request(response_payload=response_payload)

    async def _stream() -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=cfg.request_timeout_seconds) as client:
            async with client.stream("POST", url, json=chat_payload) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        yield chunk

    return _stream()
