def test_app_importable() -> None:
    from main import app

    assert app is not None


def test_post_response_proxies_and_returns_parsed_response(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from main import app
    from utils.request_formatter import format_response_request

    request_payload = {
        "model": "gpt-test",
        "instructions": "You are helpful.",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "hi"}],
            }
        ],
        "stream": True,
    }

    expected_outbound = format_response_request(response_payload=request_payload)

    stream_bytes = [b"data: hello\n\n", b"data: world\n\n"]

    captured: dict[str, object] = {}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            return

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def stream(self, method: str, url: str, *, json: dict | None = None):
            captured["method"] = method
            captured["url"] = url
            captured["json"] = json

            class _StreamCtx:
                status_code = 200

                async def __aenter__(self_inner):
                    return self_inner

                async def __aexit__(self_inner, exc_type, exc, tb):
                    return False

                def raise_for_status(self_inner) -> None:
                    return

                async def aiter_bytes(self_inner):
                    for chunk in stream_bytes:
                        yield chunk

            return _StreamCtx()

    monkeypatch.setattr("services.llm_proxy.httpx.AsyncClient", FakeAsyncClient)

    client = TestClient(app)
    resp = client.post("/response", json=request_payload)
    assert resp.status_code == 200
    assert resp.content == b"".join(stream_bytes)

    assert captured["method"] == "POST"
    assert captured["url"] == "http://localhost:8001/chat/completions"
    assert captured["json"] == expected_outbound
