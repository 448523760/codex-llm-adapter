import pytest


def test_parse_chat_completions_response_basic_text() -> None:
    from utils.response_parser import parse_chat_completions_response

    upstream = {
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

    resp = parse_chat_completions_response(upstream_payload=upstream)
    assert resp["id"] == "chatcmpl_123"
    assert resp["object"] == "response"
    assert resp["created_at"] == 1730000000
    assert resp["model"] == "gpt-test"
    assert resp["status"] == "completed"
    assert resp["usage"] == {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}
    assert resp["output"][0]["type"] == "message"
    assert resp["output"][0]["role"] == "assistant"
    assert resp["output"][0]["content"][0] == {"type": "output_text", "text": "Hello!"}


def test_parse_chat_completions_response_includes_function_calls() -> None:
    from utils.response_parser import parse_chat_completions_response

    upstream = {
        "id": "chatcmpl_456",
        "created": 1730000001,
        "model": "gpt-test",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "get_weather", "arguments": "{}"},
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }

    resp = parse_chat_completions_response(upstream_payload=upstream)
    assert resp["output"][0] == {
        "type": "function_call",
        "call_id": "call_1",
        "name": "get_weather",
        "arguments": "{}",
    }


def test_parse_chat_completions_response_rejects_missing_choices() -> None:
    from utils.response_parser import parse_chat_completions_response

    with pytest.raises(ValueError):
        parse_chat_completions_response(upstream_payload={"id": "x"})
