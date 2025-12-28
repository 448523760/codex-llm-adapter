from __future__ import annotations

from typing import Any, Iterable
from typing_extensions import NotRequired, TypedDict


class _ChatToolCallFunction(TypedDict):
    name: str
    arguments: str


class _ChatToolCall(TypedDict):
    id: str
    type: str
    function: _ChatToolCallFunction


class _ChatSystemMessage(TypedDict):
    role: str
    content: str


class _ChatAssistantMessage(TypedDict):
    role: str
    content: str | None
    tool_calls: NotRequired[list[_ChatToolCall]]


class _ChatUserMessage(TypedDict):
    role: str
    content: str | list[dict[str, Any]]


class _ChatToolMessage(TypedDict):
    role: str
    tool_call_id: str
    content: Any


ChatCompletionMessageParam = _ChatSystemMessage | _ChatAssistantMessage | _ChatUserMessage | _ChatToolMessage


def format_response_request(*, response_payload: dict[str, Any]) -> dict[str, Any]:
    """Convert public `/response` payload into OpenAI-style `/chat/completions` payload.

    Contract source of truth: `schema/response/index.md`.

    Notes:
    - This function only *formats*; it does not perform any network I/O.
    - Unknown fields are ignored and are not forwarded upstream.
    """

    model = response_payload.get("model")
    instructions = response_payload.get("instructions")
    input_items = response_payload.get("input")

    if not isinstance(model, str) or not model:
        raise ValueError("Missing or invalid required field: 'model'")
    if not isinstance(instructions, str) or not instructions:
        raise ValueError("Missing or invalid required field: 'instructions'")
    if not isinstance(input_items, list) or len(input_items) == 0:
        raise ValueError("Missing or invalid required field: 'input'")

    stream = response_payload.get("stream", True)
    if not isinstance(stream, bool):
        raise ValueError("Invalid field: 'stream' must be boolean")

    messages: list[ChatCompletionMessageParam] = []
    messages.append({"role": "system", "content": instructions})

    for item in input_items:
        if not isinstance(item, dict):
            raise ValueError("Invalid input item: expected object")

        item_type = item.get("type")
        if item_type == "message":
            messages.extend(_format_message_item(item))
        elif item_type == "function_call":
            messages.append(_format_function_call_item(item))
        elif item_type == "function_call_output":
            messages.append(_format_function_call_output_item(item))
        elif item_type == "reasoning":
            # Best-effort: ignore in Phase2; caller can decide how to surface it.
            continue
        else:
            raise ValueError(f"Unsupported input item type: {item_type!r}")

    chat_payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    # Best-effort passthrough fields supported by upstream chat schema.
    tools = response_payload.get("tools")
    if isinstance(tools, list):
        chat_payload["tools"] = tools

    parallel_tool_calls = response_payload.get("parallel_tool_calls")
    if isinstance(parallel_tool_calls, bool):
        chat_payload["parallel_tool_calls"] = parallel_tool_calls

    return chat_payload


def _format_message_item(item: dict[str, Any]) -> list[ChatCompletionMessageParam]:
    role = item.get("role")
    if role not in ("user", "assistant"):
        raise ValueError("message.role must be 'user' or 'assistant'")

    content_items = item.get("content")
    if not isinstance(content_items, list) or len(content_items) == 0:
        raise ValueError("message.content must be a non-empty array")

    has_image = any(
        isinstance(part, dict) and part.get("type") == "input_image" for part in content_items
    )

    if role == "assistant":
        if has_image:
            raise ValueError("assistant message content cannot include images")
        text = _join_text_parts(content_items, expected_part_type="input_text")
        return [{"role": "assistant", "content": text}]

    # role == user
    if not has_image:
        text = _join_text_parts(content_items, expected_part_type="input_text")
        msg: _ChatUserMessage = {"role": "user", "content": text}
        return [msg]

    # Multi-part content (text + image_url)
    multipart: list[dict[str, Any]] = []
    for part in content_items:
        if not isinstance(part, dict):
            raise ValueError("message.content[*] must be objects")
        part_type = part.get("type")
        if part_type == "input_text":
            text = part.get("text")
            if not isinstance(text, str):
                raise ValueError("input_text.text must be string")
            multipart.append({"type": "text", "text": text})
        elif part_type == "input_image":
            url = part.get("image_url")
            if not isinstance(url, str) or not url:
                raise ValueError("input_image.image_url must be non-empty string")
            multipart.append({"type": "image_url", "image_url": {"url": url}})
        else:
            raise ValueError(f"Unsupported message content part type: {part_type!r}")

    msg2: _ChatUserMessage = {"role": "user", "content": multipart}
    return [msg2]


def _format_function_call_item(item: dict[str, Any]) -> ChatCompletionMessageParam:
    call_id = item.get("call_id")
    name = item.get("name")
    arguments = item.get("arguments")

    if not isinstance(call_id, str) or not call_id:
        raise ValueError("function_call.call_id must be non-empty string")
    if not isinstance(name, str) or not name:
        raise ValueError("function_call.name must be non-empty string")
    if not isinstance(arguments, str):
        raise ValueError("function_call.arguments must be string (JSON)")

    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        ],
    }


def _format_function_call_output_item(item: dict[str, Any]) -> ChatCompletionMessageParam:
    call_id = item.get("call_id")
    output = item.get("output")
    if not isinstance(call_id, str) or not call_id:
        raise ValueError("function_call_output.call_id must be non-empty string")
    if not isinstance(output, dict):
        raise ValueError("function_call_output.output must be object")

    # Prefer explicit output.content; otherwise derive from content_items.
    content: Any
    if isinstance(output.get("content"), str):
        content = output["content"]
    else:
        content_items = output.get("content_items")
        if isinstance(content_items, list) and len(content_items) > 0:
            has_image = any(
                isinstance(part, dict) and part.get("type") == "input_image" for part in content_items
            )
            if not has_image:
                content = _join_text_parts(content_items, expected_part_type="input_text")
            else:
                multipart: list[dict[str, Any]] = []
                for part in content_items:
                    if not isinstance(part, dict):
                        raise ValueError("output.content_items[*] must be objects")
                    part_type = part.get("type")
                    if part_type == "input_text":
                        text = part.get("text")
                        if not isinstance(text, str):
                            raise ValueError("output.content_items input_text.text must be string")
                        multipart.append({"type": "text", "text": text})
                    elif part_type == "input_image":
                        url = part.get("image_url")
                        if not isinstance(url, str) or not url:
                            raise ValueError(
                                "output.content_items input_image.image_url must be non-empty string"
                            )
                        multipart.append({"type": "image_url", "image_url": {"url": url}})
                    else:
                        raise ValueError(
                            f"Unsupported output.content_items part type: {part_type!r}"
                        )
                content = multipart
        else:
            content = ""

    msg: _ChatToolMessage = {
        "role": "tool",
        "tool_call_id": call_id,
        "content": content,
    }
    return msg


def _join_text_parts(parts: Iterable[Any], *, expected_part_type: str) -> str:
    texts: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError("content part must be object")
        if part.get("type") != expected_part_type:
            raise ValueError(f"Expected content part type {expected_part_type!r}")
        text = part.get("text")
        if not isinstance(text, str):
            raise ValueError("content part text must be string")
        texts.append(text)
    return "\n".join(texts)
