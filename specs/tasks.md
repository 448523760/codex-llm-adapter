---
description: "Task list for implementing the lightweight LLM proxy service"
---

# Tasks: Lightweight LLM Proxy Service

## Phase 0: Contracts (Schemas & Translation Guides)

**Purpose**: Lock request/response contracts and mappings before building endpoints.

- [ ] T000 Define the `/response` API request/response schema and the translation guide to the upstream `/chat/completions` payload/response (single source of truth for shapes and fields).

## Phase 1: Setup (Project Initialization)

**Purpose**: Establish layout, manifests, and uv recipes described in plan.md.

- [ ] T001 Scaffold src/main.py, src/services/llm_proxy.py, src/utils/request_formatter.py, src/utils/response_parser.py, tests/test_main.py, tests/test_services/test_llm_proxy.py, tests/test_utils/test_request_formatter.py, and tests/test_utils/test_response_parser.py so the structure matches the plan.
- [ ] T002 Define dependencies, metadata, and configuration hints in project.toml for fastapi, httpx, pytest, uv, and target service settings.
- [ ] T003 [P] Create uvproject.toml with recipes for `uv project`, `uv run`, `uv test`, and `uv deps` to standardize bootstrap/run/test/deps.

## Phase 2: Foundational Utilities

**Purpose**: Provide reusable translation helpers.

- [ ] T004 [P] Implement request formatter in src/utils/request_formatter.py to convert `/response` payloads into OpenAI-style `/chat/completions` payloads.
- [ ] T005 [P] Implement response parser in src/utils/response_parser.py to map `/chat/completions` responses back to the public `/response` schema.

## Phase 3: Core Proxy (User Story 1, P1)

**Goal**: Translate `/response` → `/chat/completions`, proxy, and return the upstream response.

- [ ] T006 [P] Add integration test in tests/test_main.py that posts a sample `/response`, stubs the upstream call, asserts the translated outbound payload, and verifies the verbatim response.
- [ ] T007 [P] Add unit test in tests/test_services/test_llm_proxy.py that ensures llm_proxy uses request_formatter, sends via httpx, and returns the raw upstream response.
- [ ] T008 Implement llm_proxy in src/services/llm_proxy.py to call the configured `/chat/completions` endpoint using formatted payloads and return the response data.
- [ ] T009 Implement the `/response` route in src/main.py to forward to llm_proxy and apply response_parser as needed before returning.

## Phase 4: Reliability & Observability (User Story 2, P2)

**Goal**: Structured logging and meaningful HTTP statuses on failures.

- [ ] T010 [P] Add regression test in tests/test_main.py that simulates httpx timeout/failure and asserts descriptive HTTP status/body.
- [ ] T011 Update src/main.py to log inbound requests/responses and register exception handlers that map httpx/validation errors to HTTP statuses with context.
- [ ] T012 Update src/services/llm_proxy.py to log outbound payloads/responses and raise descriptive exceptions for failed proxied calls.

## Phase 5: Configurable Targets (User Story 3, P3)

**Goal**: Support multiple target LLM services with HTTP/HTTPS enforcement.

- [ ] T013 [P] Add tests in tests/test_services/test_llm_proxy.py verifying target selection and protocol enforcement.
- [ ] T014 Create src/config.py to load target definitions (endpoints, protocol, defaults) from project.toml/env and expose them to llm_proxy.
- [ ] T015 Update src/services/llm_proxy.py to consume configuration, select targets, and honor per-target protocol/headers when issuing httpx requests.
- [ ] T016 Extend project.toml with `[tool.llm_proxy.targets]` metadata for target services, defaults, and required headers.

## Phase 6: Polish & Operations

**Purpose**: Document contracts, centralize logging config, and harden performance.

- [ ] T017 [P] Document the `/response` contract, configuration knobs, and uv recipes in README.md (include the translation guide from T000).
- [ ] T018 [P] Add shared logging configuration in src/logging_config.py and wire it into src/main.py.
- [ ] T019 [P] Harden src/services/llm_proxy.py with configurable httpx timeouts/retries/pooling and capture recommendations in README.md.

## Dependencies & Execution Order

- Phase 0 locks schemas; Phase 1 sets the skeleton and manifests; Phase 2 delivers utilities; Phase 3 (P1) builds the proxy; Phase 4 (P2) adds reliability; Phase 5 (P3) adds target configurability; Phase 6 polishes.
- Tests precede or accompany implementations within each phase (e.g., T006/T007 before T008/T009).
- Parallelism: T002/T003, T004/T005, and T013 alongside T014–T016 can run in parallel because they touch separate areas.