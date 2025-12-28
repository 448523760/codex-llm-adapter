from __future__ import annotations

from typing import Any


def format_response_request(*, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Convert public `/response` payload into OpenAI-style `/chat/completions` payload.

    Phase 1 scaffolding only; implemented in later phases.
    """

    raise NotImplementedError
