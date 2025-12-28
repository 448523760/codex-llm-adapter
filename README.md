# codex-llm-adapter

The llm adapter for codex-cli

## Background

The openai [codex](https://github.com/openai/codex) project will discontinue support for the `chat/completions` interface in February 2026. This change will impact users relying on open-source models or LLMs that do not support the `response` API, making it impossible to continue using Codex with these models. This project was created to ensure that such users can continue leveraging Codex by bridging the gap to the `chat/completions` API.

## Project Overview

This project is a lightweight LLM proxy service. It exposes a `/response` API to external clients while internally forwarding requests to the `chat/completions` API. This ensures seamless compatibility with Codex. For details on the transformation logic, refer to the subsequent documentation.
