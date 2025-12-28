import pytest


def test_format_response_request_basic_text_message() -> None:
    from utils.request_formatter import format_response_request

    payload = {
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

    chat_payload = format_response_request(response_payload=payload)
    assert chat_payload["model"] == "gpt-test"
    assert chat_payload["stream"] is True
    assert chat_payload["messages"][0] == {"role": "system", "content": "You are helpful."}
    assert chat_payload["messages"][1] == {"role": "user", "content": "hi"}


def test_format_response_request_user_message_with_image_becomes_multipart() -> None:
    from utils.request_formatter import format_response_request

    payload = {
        "model": "gpt-test",
        "instructions": "You are helpful.",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "describe this"},
                    {"type": "input_image", "image_url": "https://example.com/a.png"},
                ],
            }
        ],
    }

    chat_payload = format_response_request(response_payload=payload)
    user_msg = chat_payload["messages"][1]
    assert user_msg["role"] == "user"
    assert isinstance(user_msg["content"], list)
    assert user_msg["content"][0] == {"type": "text", "text": "describe this"}
    assert user_msg["content"][1] == {
        "type": "image_url",
        "image_url": {"url": "https://example.com/a.png"},
    }


def test_format_response_request_function_call_and_output() -> None:
    from utils.request_formatter import format_response_request

    payload = {
        "model": "gpt-test",
        "instructions": "You are helpful.",
        "input": [
            {
                "type": "function_call",
                "call_id": "call_1",
                "name": "get_weather",
                "arguments": "{\"city\":\"Shanghai\"}",
            },
            {
                "type": "function_call_output",
                "call_id": "call_1",
                "output": {"content": "sunny"},
            },
        ],
        "parallel_tool_calls": False,
        "tools": [{"type": "function", "function": {"name": "get_weather"}}],
    }

    chat_payload = format_response_request(response_payload=payload)
    assert chat_payload["parallel_tool_calls"] is False
    assert chat_payload["tools"] == [{"type": "function", "function": {"name": "get_weather"}}]
    assistant_msg = chat_payload["messages"][1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["content"] is None
    assert assistant_msg["tool_calls"][0]["id"] == "call_1"
    assert assistant_msg["tool_calls"][0]["function"]["name"] == "get_weather"
    tool_msg = chat_payload["messages"][2]
    assert tool_msg["role"] == "tool"
    assert tool_msg["tool_call_id"] == "call_1"
    assert tool_msg["content"] == "sunny"


def test_format_response_request_assistant_message_joins_text_parts() -> None:
    from utils.request_formatter import format_response_request

    payload = {
        "model": "gpt-test",
        "instructions": "You are helpful.",
        "input": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "input_text", "text": "line1"},
                    {"type": "input_text", "text": "line2"},
                ],
            }
        ],
    }

    chat_payload = format_response_request(response_payload=payload)
    assert chat_payload["messages"][1] == {"role": "assistant", "content": "line1\nline2"}


def test_format_response_request_rejects_assistant_images() -> None:
    from utils.request_formatter import format_response_request

    payload = {
        "model": "gpt-test",
        "instructions": "You are helpful.",
        "input": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "input_text", "text": "nope"},
                    {"type": "input_image", "image_url": "https://example.com/a.png"},
                ],
            }
        ],
    }

    with pytest.raises(ValueError):
        format_response_request(response_payload=payload)


def test_format_response_request_rejects_missing_required_fields() -> None:
    from utils.request_formatter import format_response_request

    with pytest.raises(ValueError):
        format_response_request(response_payload={})
