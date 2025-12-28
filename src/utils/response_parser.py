from __future__ import annotations

from typing import Any


def parse_chat_completions_response(*, upstream_payload: dict[str, Any]) -> dict[str, Any]:
    """Map upstream `/chat/completions` response back to public `/response` schema.

    Phase 1 scaffolding only; implemented in later phases.
    """

    raise NotImplementedError
