# Specification

## Overview
This document outlines the requirements for the lightweight LLM proxy service. The service will expose a `/response` endpoint to clients while internally proxying requests to target LLM services through their native `/chat/completions` interface.

## Functional Requirements
- Expose a `/response` endpoint for client requests.
- Translate incoming requests into the format required by the target LLM service.
- Proxy requests to the target LLM service's `/chat/completions` endpoint.
- Return the response from the target LLM service to the client.

## Non-Functional Requirements
- Provide robust error handling for failed or malformed requests.
- Log all requests and responses for debugging and monitoring purposes.

## Integration Details
- Support multiple target LLM services with configurable endpoints.
- Use HTTP/HTTPS for communication with target services.
- Ensure compatibility with OpenAI's API specifications.

## Contracts
- `/response` request schema (single source of truth): see `specs/response_api_request_schema.md`.
