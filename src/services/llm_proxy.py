from __future__ import annotations

from typing import Any


async def proxy_response(*, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Proxy a public `/response` payload to an upstream `/chat/completions`.

    Phase 1 scaffolding only; implemented in later phases.
    """

    raise NotImplementedError
