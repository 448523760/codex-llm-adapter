# Schema Index

本目录定义本项目涉及的两套接口契约（schema）：

1. **上游 Chat API**：本项目实际要调用的 OpenAI 风格 `/chat/completions`（或兼容实现）。
2. **对外 Response API**：本项目对客户端暴露的 `/response`（语义上参考 OpenAI `Responses API`）。

> 适配目标：将**对外的 Response 形状**翻译为**上游 Chat Completions 形状**，并将上游结果再映射回对外 Response 形状。

## References

本项目的 schema 设计**参考** OpenAI 官方 API Reference（作为字段命名、数据结构、行为语义的主要来源）：

- https://platform.openai.com/docs/api-reference/chat
- https://platform.openai.com/docs/api-reference/responses

说明：本仓库实现的是“适配器/代理”，并不保证覆盖 OpenAI 文档里的全部字段；本目录会明确列出支持范围与不兼容项。

## Files

- [chat/index.md](chat/index.md): 上游 `/chat/completions` 请求/响应 schema（以本适配器真正会构造/依赖的字段为准）。
- [response/index.md](response/index.md): 对外 `/response` 请求/响应 schema（以本适配器对外承诺的字段为准）。

## Adapter Compatibility Notes

因为本项目是把 **Chat** 封装成 **Response** 的适配层，二者存在天然不匹配：

- **状态/续写能力差异**：OpenAI Responses API 里存在用于“接续上一次 response”的概念（例如 `previous_response_id`）。
	但 Chat Completions 本质是“无状态请求”（服务端不替你保存会话），本适配器也不维护对话存储。
	因此此类字段在本项目里**没有可实现的语义**。
  
	适配策略：
	- **本项目 schema 中不包含这些字段**（不对外承诺）。
	- 客户端需要“续写/上下文”时，应将完整上下文放回 `input/messages` 中显式传入。

- **工具调用形状差异**：Responses API 的 tool/call/output 事件模型与 Chat Completions 的 `tool_calls`/`tool` role message 模型不同。
	本适配器会做**最小必要映射**以满足代理调用（仅覆盖 OpenAI 标准的 function tools 形态）。

## Mapping Overview (High Level)

- `ResponseRequest.model` → `ChatCompletionsRequest.model`
- `ResponseRequest.instructions` → `messages[0] = {"role":"system","content": instructions}`
- `ResponseRequest.input[]` → `ChatCompletionsRequest.messages[]`（按 item 类型映射为 user/assistant/tool 消息及 tool_calls）
