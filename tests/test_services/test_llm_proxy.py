import pytest


def test_llm_proxy_importable() -> None:
    from services import llm_proxy

    assert llm_proxy is not None


@pytest.mark.asyncio
async def test_proxy_response_formats_and_posts(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.llm_proxy import proxy_response

    captured: dict[str, object] = {}

    def fake_format_response_request(*, response_payload: dict) -> dict:
        captured["formatted_from"] = response_payload
        return {"model": "m", "messages": [{"role": "system", "content": "i"}], "stream": False}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return

        def json(self) -> dict:
            return {"id": "chatcmpl_x", "choices": [{"message": {"role": "assistant", "content": "ok"}}]}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            captured["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, *, json: dict | None = None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("services.llm_proxy.format_response_request", fake_format_response_request)
    monkeypatch.setattr("services.llm_proxy.httpx.AsyncClient", FakeAsyncClient)

    upstream = await proxy_response(response_payload={"model": "x", "instructions": "y", "input": []})
    assert upstream["id"] == "chatcmpl_x"
    assert captured["formatted_from"] == {"model": "x", "instructions": "y", "input": []}
    assert captured["url"] == "http://localhost:8001/chat/completions"
    assert captured["json"] == {"model": "m", "messages": [{"role": "system", "content": "i"}], "stream": False}
