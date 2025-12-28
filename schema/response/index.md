# Response API Schema (Public)

本文件定义本项目对外暴露的 `/response` 接口 schema。

- 语义参考：https://platform.openai.com/docs/api-reference/responses
- 适配背景：本项目内部实际调用的是上游 `/chat/completions`（见 [chat/index.md](../chat/index.md)）。因此对外的 Response schema 必须在“尽量像 OpenAI Responses”与“能被 Chat 无状态实现”之间做取舍。

---

## Endpoint

- Method: `POST`
- Path (public): `/response`

---

## ResponseRequest (Adapter Contract)

### Top-level shape

```json
{
  "model": "gpt-xxx",
  "instructions": "You are a helpful assistant.",
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": [
        {"type": "input_text", "text": "hi"}
      ]
    }
  ],
  "tools": [],
  "parallel_tool_calls": false,
  "reasoning": null,
  "include": [],
  "text": null,
  "prompt_cache_key": null,
  "stream": true
}
```

### Fields

- `model` (string, required)
  - 目标模型名。
- `instructions` (string, required)
  - 系统指令。适配时会变成上游 Chat 的第一条 `system` message。
- `input` (array of `ResponseItem`, required)
  - 对话/事件输入序列。适配时会被转换成上游 Chat `messages` 与 `tool_calls`。
- `tools` (array, optional)
  - 工具定义列表。适配时会尽量透传给上游 Chat 的 `tools`。
- `parallel_tool_calls` (boolean, optional; default `false`)
  - 是否允许并行工具调用。
- `reasoning` (object|null, optional)
  - 推理控制（如果客户端需要表达“推理强度/偏好”，可放在这里）。
- `include` (array of string, optional)
  - 用于请求额外字段/调试信息的列表（adapter 可能忽略部分 include）。
- `text` (object|null, optional)
  - 文本输出控制（例如格式/截断策略等）。
- `prompt_cache_key` (string|null, optional)
  - 提示缓存键（adapter 可能透传或忽略，取决于 provider）。
- `stream` (boolean, optional; default `true`)
  - 是否以流式返回。Phase0 里按 streaming 作为主要交互方式。

---

## ResponseItem

`input[]` 由多种 item 组成；本项目以“能映射到 Chat messages/tool_calls”为准。

### 1) Message item

```json
{
  "type": "message",
  "id": "optional-id",
  "role": "user | assistant",
  "content": [
    {"type": "input_text", "text": "hello"},
    {"type": "input_image", "image_url": "https://..."}
  ]
}
```

- `role=user`：会映射为上游 `role=user` message。
- `role=assistant`：会映射为上游 `role=assistant` message（通常 `content` 会被拼成 string）。

### 2) FunctionCall item

表示 assistant 发起函数工具调用：

```json
{
  "type": "function_call",
  "id": "optional-id",
  "call_id": "call_...",
  "name": "tool_name",
  "arguments": "{...}"
}
```

适配到上游：assistant message + `tool_calls[{type:function,...}]`。

### 3) FunctionCallOutput item

表示 tool 执行结果：

```json
{
  "type": "function_call_output",
  "call_id": "call_...",
  "output": {
    "content": "...",
    "content_items": [
      {"type": "input_text", "text": "..."}
    ]
  }
}
```

适配到上游：`role=tool` message，携带 `tool_call_id` 与 `content`。

### 4) Reasoning item (Best-effort)

`reasoning`/`reasoning item` 在 Responses API 语义上是事件/元信息。
但 Chat Completions 并没有标准化的“reasoning item”输入模型。

适配策略：
- 在不破坏对话顺序的前提下，adapter 可能把 reasoning 文本**附着**到相邻的 assistant/tool_call 上（例如作为扩展字段 `reasoning` 或拼接到文本里）。
- 对于无法安全映射的 reasoning item，adapter 可能直接忽略。

---

## ResponseResponse (Public Response Shape)

对外返回值目标形状参考 OpenAI Responses API：

```json
{
  "id": "resp_...",
  "object": "response",
  "created_at": 1730000000,
  "model": "gpt-xxx",
  "status": "completed",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {"type": "output_text", "text": "Hello!"}
      ]
    }
  ],
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  }
}
```

> 注意：本项目内部上游是 Chat Completions，因此某些 Responses API 的输出事件类型（更细粒度的 tool/trace 事件流）可能无法 1:1 还原；adapter 会以“message + 必要工具调用结果”为主。

---

## Explicit Omissions / Incompatibilities (Must Know)

以下字段在 OpenAI Responses API 中存在，但**本项目不会纳入对外 schema**（也不对外承诺）：

- `previous_response_id`
  - 原因：Chat Completions 无状态，本项目也不提供 response 级别的服务端会话存储。
  - 替代方案：客户端应将上下文显式放入 `input`。

以下字段可能因 provider 能力而被忽略或拒绝（不建议依赖）：

- `store`（服务端存储/持久化）
- `background` / 异步作业相关字段
- 部分 `include` 选项（adapter 只保证最小集合）

---

## Mapping Summary

- `instructions` → 上游 `messages[0] = {"role":"system","content": instructions}`
- `input[].type=message(role=user)` → 上游 `role=user` message
- `input[].type=message(role=assistant)` → 上游 `role=assistant` message（多段文本会被拼接）
- `function_call` → 上游 assistant `tool_calls[type=function]`
- `function_call_output` → 上游 `role=tool` message
