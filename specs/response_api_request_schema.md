---
Deprecated: since it not necessary
---

# `/response` API — Request Schema (Contract)

## Goal
This adapter exposes a **public** `POST /response` endpoint (Codex-facing) and will translate the request into an upstream **OpenAI-style** `POST /chat/completions` payload.

This document defines the **request contract** for `POST /response`.

## Endpoint
- **Method**: `POST`
- **Path**: `/response`
- **Content-Type**: `application/json`

## Request Object: `ResponseRequest`

### Design notes
- The schema is intentionally **compatible with the shape of OpenAI "Responses API" style inputs** (e.g., `input`, `max_output_tokens`) while keeping translation to `/chat/completions` straightforward.
- Unknown top-level fields:
  - SHOULD be ignored for forward-compatibility.
  - MUST NOT be forwarded upstream unless explicitly mapped.

### Fields
| Field | Type | Required | Default | Notes |
|---|---:|:---:|:---:|---|
| `input` | `string` \| `InputItem[]` | ✅ | — | Primary user input. See `InputItem` below. |
| `model` | `string` | ⛔ | target default | Logical model name. Passed through to upstream `model` when present. |
| `target` | `string` | ⛔ | config default | Target service key (Phase 5). If absent, use default target. |
| `max_output_tokens` | `integer` | ⛔ | upstream default | Translates to upstream `max_tokens`. Must be `>= 1`. |
| `temperature` | `number` | ⛔ | upstream default | `0.0` to `2.0` recommended range. |
| `top_p` | `number` | ⛔ | upstream default | `0.0` to `1.0` recommended range. |
| `presence_penalty` | `number` | ⛔ | upstream default | Typical range `-2.0` to `2.0`. |
| `frequency_penalty` | `number` | ⛔ | upstream default | Typical range `-2.0` to `2.0`. |
| `stop` | `string` \| `string[]` | ⛔ | — | Translates to upstream `stop`. |
| `stream` | `boolean` | ⛔ | `false` | This service initially only supports `false`. If `true`, the server SHOULD reject with `400` (until streaming is implemented). |
| `metadata` | `object` | ⛔ | — | Opaque client metadata (for logging/correlation). Not forwarded upstream by default. |
| `user` | `string` | ⛔ | — | Optional end-user identifier (OpenAI-compatible field). |

## Input Types

### `InputItem`
`InputItem` represents an element in the structured `input` array.

Supported item types (initially):
- `message`: a chat message with `role` and `content`.

### `MessageInputItem`
| Field | Type | Required | Notes |
|---|---:|:---:|---|
| `type` | `"message"` | ✅ | Discriminator. |
| `role` | `"system" \| "user" \| "assistant"` | ✅ | Upstream `/chat/completions` supports these roles. |
| `content` | `string` | ✅ | Plain text content (MVP). |

## Examples

### Example A — simple string input
```json
{
  "model": "gpt-4.1-mini",
  "input": "Write a haiku about rust and fastapi."
}
```

### Example B — structured messages
```json
{
  "target": "local-llm",
  "model": "some-model",
  "input": [
    {"type": "message", "role": "system", "content": "You are a helpful coding assistant."},
    {"type": "message", "role": "user", "content": "Explain why HTTP timeouts matter."}
  ],
  "max_output_tokens": 256,
  "temperature": 0.2,
  "stream": false,
  "metadata": {"request_id": "abc-123"}
}
```

## Machine-readable JSON Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.invalid/schemas/response-request.schema.json",
  "title": "ResponseRequest",
  "type": "object",
  "required": ["input"],
  "properties": {
    "input": {
      "description": "Primary user input.",
      "oneOf": [
        {"type": "string", "minLength": 1},
        {
          "type": "array",
          "minItems": 1,
          "items": {"$ref": "#/$defs/InputItem"}
        }
      ]
    },
    "model": {"type": "string", "minLength": 1},
    "target": {"type": "string", "minLength": 1},

    "max_output_tokens": {"type": "integer", "minimum": 1},
    "temperature": {"type": "number"},
    "top_p": {"type": "number"},
    "presence_penalty": {"type": "number"},
    "frequency_penalty": {"type": "number"},

    "stop": {
      "oneOf": [
        {"type": "string"},
        {"type": "array", "items": {"type": "string"}}
      ]
    },

    "stream": {"type": "boolean", "default": false},
    "metadata": {"type": "object"},
    "user": {"type": "string"}
  },
  "additionalProperties": true,
  "$defs": {
    "InputItem": {
      "oneOf": [
        {"$ref": "#/$defs/MessageInputItem"}
      ]
    },
    "MessageInputItem": {
      "type": "object",
      "required": ["type", "role", "content"],
      "properties": {
        "type": {"const": "message"},
        "role": {"enum": ["system", "user", "assistant"]},
        "content": {"type": "string"}
      },
      "additionalProperties": true
    }
  }
}
```
