# ADR-013 — Communication Provider Abstraction

Status: Accepted  
Scope: Backend communication transport infrastructure  
Supersedes: (none)  
Related: ADR-010 (session boundaries), ADR-011 (CommunicationSession lifecycle)

This record captures the requested Communication Provider Abstraction
(originally proposed as ADR-004). Repository ADRs are numbered sequentially
from ADR-008; this decision is therefore ADR-013.

## Context

Yara needs real-time voice and video between the Family App, the Hub, and
the elder. A third-party conference service (currently Skyroom) supplies the
media rooms.

The Communication Domain Contract already owns `CommunicationSession`,
participants, call attempts, and outcomes. That aggregate is a **per-call**
lifecycle. The conference vendor, by contrast, expects rooms and users to be
created once and reused.

If Skyroom types, URLs, or the API key leak into the Communication domain,
Hub, or Family App, replacing the vendor later (LiveKit, Janus, Jitsi)
would rewrite domain models and client code. The Hub must never call the
vendor REST API or store the vendor API key.

## Decision

1. **Skyroom is an Infrastructure Provider**, not a domain concept.
   Communication has no Skyroom types, endpoints, or credentials.

2. **Backend is the only authority** for vendor credentials and for room
   and user lifecycle. The API key stays in Backend configuration
   (`SKYROOM_API_KEY`). It is never returned to clients and never shipped
   in the Hub or Family App.

3. **Hub and Family App speak only to Backend for session control.** They
   receive opaque join credentials (`sessionId`, `joinToken`, `expiresAt`).
   They never call Skyroom REST and never hold the API key.
   `joinToken` is provider-agnostic. The Hub media adapter
   (`SkyroomCallEngine`) only consumes that token as `loginUrl`.

4. **Provider port, not vendor types.** Backend depends on a
   `CommunicationProvider` protocol:

   - ensure (create or reuse) room
   - ensure (create or reuse) user
   - generate login URL
   - close room (teardown only)

   `SkyroomCommunicationProvider` is the current adapter. A future LiveKit,
   Janus, or Jitsi adapter can replace it without changing Communication
   aggregates, commands, events, or client contracts.

5. **Persistent vendor room ≠ CommunicationSession.**
   One Elder has one provider room, reused for every call.
   Each call still creates a new `CommunicationSession`.
   Vendor room and user identifiers are stored in infrastructure bindings,
   not on the frozen `CommunicationSession` aggregate.
   Ending a call ends the session; it does not delete the provider room.

6. **One active session per Elder.** Concurrent `start_call` while a session
   is `INITIATED`, `CONNECTING`, or `CONNECTED` returns HTTP 409.
   A second caregiver joins an in-progress call via `login-url` (a new
   `joinToken` for the same session), not by starting a second session.

7. **Unjoined sessions auto-cancel.** If nobody connects within
   `COMMUNICATION_SESSION_JOIN_TIMEOUT_SECONDS` (default 120), Backend
   cancels the session (`CANCELLED`). Credential TTL (`joinToken` expiry)
   is independent of this session timeout.

## Audit (facts already owned; join/leave timestamps later)

Medical audit of a call maps to existing Communication facts:

| Audit need | Current owner |
|---|---|
| Call requested | `CommunicationSessionInitiated` |
| Call started | `CallAttemptStarted` + session `CONNECTING` |
| Call joined | `CommunicationSessionConnected` + `connected_at` |
| Call finished | `CommunicationSessionEnded` (or Missed/Declined/Failed/Cancelled) |
| Duration | `connected_at` → `ended_at` |
| Who | `SessionParticipant` |

Participant `joined_at` / `left_at` are **not** added in this phase. When
media join/leave is implemented, those timestamps belong on
`SessionParticipant` (or a future CallAudit entity), not on Skyroom.

## Consequences

- Communication Domain remains replaceable at the transport layer.
- Clients stay thin: JWT to Backend, then use the opaque `joinToken`.
- Room reuse matches vendor guidance and avoids quota/rate-limit waste.
- Switching providers is an infrastructure change, not a domain rewrite.
- The elder experiences at most one active call at a time.
