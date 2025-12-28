def test_app_importable() -> None:
    from main import app

    assert app is not None


def test_post_response_proxies_and_returns_parsed_response(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from main import app
    from utils.request_formatter import format_response_request
    from utils.response_parser import parse_chat_completions_response

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
        "stream": False,
    }

    expected_outbound = format_response_request(response_payload=request_payload)

    upstream_payload = {
        "id": "chatcmpl_123",
        "object": "chat.completion",
        "created": 1730000000,
        "model": "gpt-test",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
    }

    expected_public = parse_chat_completions_response(upstream_payload=upstream_payload)

    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return

        def json(self) -> dict:
            return upstream_payload

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            return

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, *, json: dict | None = None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("services.llm_proxy.httpx.AsyncClient", FakeAsyncClient)

    client = TestClient(app)
    resp = client.post("/response", json=request_payload)
    assert resp.status_code == 200
    assert resp.json() == expected_public

    assert captured["url"] == "http://localhost:8001/chat/completions"
    assert captured["json"] == expected_outbound
