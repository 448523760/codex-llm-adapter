from __future__ import annotations

from typing import Any


def parse_chat_completions_response(*, upstream_payload: dict[str, Any]) -> dict[str, Any]:
    """Map upstream `/chat/completions` response back to public `/response` schema.

    Contract source of truth: `schema/response/index.md`.

    This is a best-effort conversion from Chat Completions into a Responses-like
    shape. Some Responses API event types cannot be reconstructed from a single
    chat completion response.
    """

    if not isinstance(upstream_payload, dict):
        raise ValueError("upstream_payload must be an object")

    upstream_id = upstream_payload.get("id")
    created = upstream_payload.get("created")
    model = upstream_payload.get("model")

    choices = upstream_payload.get("choices")
    if not isinstance(choices, list) or len(choices) == 0:
        raise ValueError("Invalid upstream response: missing 'choices'")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ValueError("Invalid upstream response: choices[0] must be object")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise ValueError("Invalid upstream response: choices[0].message must be object")

    reasoning_parts = _extract_reasoning_parts(message.get("reasoning_content"))
    role = message.get("role", "assistant")
    if role not in ("assistant", "tool"):
        # We only expose Responses-like assistant output here.
        role = "assistant"

    reasoning_attached = False
    output_items: list[dict[str, Any]] = []

    # 1) Assistant textual content
    content = message.get("content")
    if isinstance(content, str) and content != "":
        message_item: dict[str, Any] = {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": content}],
        }
        if reasoning_parts:
            message_item["reasoning"] = reasoning_parts
            reasoning_attached = True
        output_items.append(message_item)
    elif content is None:
        # tool_call-only assistant message; handled below
        pass
    elif content == "":
        pass

    # 2) Tool calls (function)
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list):
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            if call.get("type") != "function":
                continue
            call_id = call.get("id")
            fn = call.get("function")
            if not isinstance(fn, dict):
                continue
            name = fn.get("name")
            arguments = fn.get("arguments")
            if isinstance(name, str) and isinstance(arguments, str) and isinstance(call_id, str):
                call_item: dict[str, Any] = {
                    "type": "function_call",
                    "call_id": call_id,
                    "name": name,
                    "arguments": arguments,
                }
                if reasoning_parts and not reasoning_attached:
                    call_item["reasoning"] = reasoning_parts
                    reasoning_attached = True
                output_items.append(call_item)

    if reasoning_parts and not reasoning_attached:
        output_items.append(
            {"type": "message", "role": role, "content": [], "reasoning": reasoning_parts}
        )

    usage_in = 0
    usage_out = 0
    usage_total = 0
    usage = upstream_payload.get("usage")
    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if isinstance(prompt_tokens, int):
            usage_in = prompt_tokens
        if isinstance(completion_tokens, int):
            usage_out = completion_tokens
        if isinstance(total_tokens, int):
            usage_total = total_tokens
        else:
            usage_total = usage_in + usage_out
    else:
        usage_total = 0

    response: dict[str, Any] = {
        "id": upstream_id if isinstance(upstream_id, str) and upstream_id else "resp_unknown",
        "object": "response",
        "created_at": int(created) if isinstance(created, (int, float)) else 0,
        "model": model if isinstance(model, str) else "",
        "status": "completed",
        "output": output_items,
        "usage": {
            "input_tokens": usage_in,
            "output_tokens": usage_out,
            "total_tokens": usage_total,
        },
    }

    return response


def _extract_reasoning_parts(reasoning_content: Any) -> list[dict[str, str]]:
    parts: list[dict[str, str]] = []
    if isinstance(reasoning_content, str):
        if reasoning_content:
            parts.append({"type": "output_text", "text": reasoning_content})
    elif isinstance(reasoning_content, list):
        for chunk in reasoning_content:
            if not isinstance(chunk, dict):
                continue
            if chunk.get("type") != "text":
                continue
            text = chunk.get("text")
            if isinstance(text, str) and text:
                parts.append({"type": "output_text", "text": text})
    return parts
