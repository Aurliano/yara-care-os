# Yara Backend Implementation Plan

**Status:** Active  
**Architecture:** Modular Monolith  
**Source of Truth:** AGENTS.md + Architecture + ERD V2.1 + Frozen Domain Contracts

## Execution Stages

| Stage | Scope |
|---|---|
| B0 | Backend Foundation + Architecture Guardrails |
| B1 | Identity & Access |
| B2 | Licensing |
| B3 | Event Foundation |
| B4 | Scheduling |
| B5 | Workflow Engine |
| B6 | Care |
| B7 | Device |
| B8 | Communication |
| B9 | Synchronization & Hub API |
| B10 | MVP Application APIs |
| B11 | Hardening |

## Execution Rule

Stages are implemented incrementally.

For each stage:

1. Read AGENTS.md.
2. Read this implementation plan.
3. Read only the relevant Domain Contract(s), ERD section, ADRs, and architecture documentation.
4. Inspect existing implementation before modifying it.
5. Implement only the requested stage.
6. Run functional tests.
7. Run architecture/boundary checks.
8. Review the diff against relevant Frozen Domain Contracts.
9. Report results.
10. Stop before starting the next stage.

A later stage may depend on an earlier stage, but must not be implemented prematurely.

## Conflict Rule

Frozen Domain Contracts and approved ADRs are authoritative.

If implementation requires violating or changing a Frozen decision:

**STOP and report the conflict.**

Do not silently modify the architecture, schema, dependency direction, or Domain Contract.

## Review Gates

Architecture review is especially important after:

- B5 — Workflow
- B6 — Care
- B7 — Device
- B9 — Synchronization

These stages introduce critical cross-domain behavior and should not proceed to the next stage until their architecture checks pass.

## Current Stage

**Completed** (B0–B11)

Sprint III Phase A adds Backend communication *transport* infrastructure
without changing frozen Communication aggregates:

- `CommunicationProvider` port (ADR-013)
- Skyroom adapter (API key, room/user reuse, opaque `joinToken`)
- `POST /api/v1/communication/call/start|end` and `POST /api/v1/communication/login-url`
- One active session per Elder (409 on conflict)
- Auto-cancel of unjoined sessions after the join timeout

Sprint III Phase B connects Hub Runtime (`CommunicationGateway`,
`CommunicationRepository`, `CommunicationRuntime`) to those Backend APIs.
The Hub persists the current `CallSession` for reconnect and process-death
recovery.

Sprint III Phase C adds Hub `SkyroomCallEngine`. The Hub consumes the
Backend `joinToken` as `loginUrl` and never calls Skyroom REST.

Sprint III Phase D is Hub presentation only. It maps Communication Runtime
states to elder call screens (incoming, outgoing, talking, finished,
connection lost, retry) without changing runtime or Backend APIs.

