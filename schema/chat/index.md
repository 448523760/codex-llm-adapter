# Chat API Schema (Upstream)

本文件描述本项目将要调用的上游 OpenAI 风格 **Chat Completions** 接口 schema。

- 参考：https://platform.openai.com/docs/api-reference/chat
- 本项目定位：**适配器**。因此这里不是“完整 OpenAI schema”，而是“本项目会构造、会依赖、会透传”的字段集合。

---

## Endpoint

- Method: `POST`
- Path (upstream): `/v1/chat/completions`

> 注意：不同 provider 可能路径不同，但 payload 形状按 OpenAI 风格组织。

---

## ChatCompletionsRequest (Subset Used By This Adapter)

本适配器在上游请求里至少会构造以下字段（来自仓库内的请求构造逻辑 `external/codex-api/chat.rs` 的等价形状）：

```json
{
  "model": "gpt-xxx",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "stream": true,
  "tools": []
}
```

### Fields

- `model` (string, required)
  - 上游模型名。
- `messages` (array, required)
  - 见下方 `ChatMessage`。
- `stream` (boolean, required in this adapter)
  - 本适配器默认按 streaming 方式与上游交互（实现上可能固定为 `true`）。
- `tools` (array, optional)
  - 工具定义数组；内容结构通常遵循 OpenAI `tools` 规范（例如 `type=function`）。

> 说明：OpenAI Chat API 还有诸如 `temperature`、`top_p`、`max_tokens`、`response_format`、`tool_choice` 等字段；本适配器在 Phase0 先不把它们当做“必须支持的对外契约”。未来如果需要，可在 Response schema 里补充并映射。

---

## ChatMessage

`messages[]` 中的元素通常具有以下通用形状：

```json
{
  "role": "user | system | assistant | tool",
  "content": "..." 
}
```

### `role = system`

- `content`: string

本适配器会把对外 `ResponseRequest.instructions` 写入第一条 system message。

### `role = user`

- `content`: string **或** multi-part 数组（文本+图片）

当包含图片时，本适配器会构造类似：

```json
{
  "role": "user",
  "content": [
    {"type": "text", "text": "Describe this"},
    {"type": "image_url", "image_url": {"url": "https://..."}}
  ]
}
```

### `role = assistant`

- `content`: string 或 `null`
- `tool_calls` (optional)

工具调用（function）示例：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_...",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\":\"Shanghai\"}"
      }
    }
  ]
}
```

### `role = tool`

用于回传工具执行输出，典型形状：

```json
{
  "role": "tool",
  "tool_call_id": "call_...",
  "content": "tool output" 
}
```

当 tool output 包含多模态内容时，`content` 也可能是数组（text/image_url parts）。

---

## ChatCompletionsResponse (High Level)

OpenAI 风格 Chat Completions 响应通常包含：

- `id` (string)
- `object` (string, 常见为 `chat.completion`)
- `created` (number)
- `model` (string)
- `choices` (array)
  - `choice.message` / `choice.delta`（streaming）
  - `choice.finish_reason`
- `usage` (object)

本适配器在 Phase0 的重点是**请求翻译**与**最小必要字段透传**；具体哪些响应字段会被保留/如何映射，见 [response/index.md](../response/index.md) 的“mapping/兼容性”章节。
