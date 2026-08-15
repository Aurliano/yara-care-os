# ADR-012 — Hub Reminder MVP (Local Runtime)

Status: Accepted (MVP slice)  
Scope: Android Hub — medication reminder execution path

## Context

The Hub must show medication reminders offline and accept elder interactions locally. Full backend workflow sync, escalation, and production UI polish are not yet complete.

## Decisions

**Decision 1 — Local workflow bootstrap**  
If `WorkflowDefinition` is missing on the replica but referenced by a `CareActivity`, the Hub creates a minimal local `SHOW_REMINDER` definition (`HubWorkflowBootstrap`).  
Reason: sync may stage care activities before workflow definitions on some paths; reminders must still run offline.

**Decision 2 — Reminder pipeline ownership**  
Scheduling marks occurrences `DUE`; workflow starts execution; `SHOW_REMINDER` opens UI + notification; confirm enqueues `HUB_CONFIRMATION` pending evidence.  
Reason: matches Workflow domain contract; backend remains source of truth for care meaning.

**Decision 3 — Postpone is local-first in MVP**  
Postpone reads policy from workflow definition JSON (`allowed`, `max_count`, `delay_seconds`), reschedules the occurrence to `SCHEDULED`, re-arms alarm, and releases in-memory reminder dispatch so the screen can fire again.  
Reason: postpone is not completion; schedule definition is unchanged; cloud upload of postpone facts is deferred.

**Decision 4 — Developer Settings stays in debug builds**  
Force sync, schedule-local-test (1 min), and diagnostic export remain available for field debugging.  
Reason: app is not production-complete; real-time QA and backend scheduling integration are follow-up work.

**Decision 5 — Deferred to next slices**  
- Reminder UI polish and accessibility pass  
- Backend-authoritative scheduling (reduce local test/bootstrap reliance)  
- Upload/sync of postpone and full execution lifecycle events  
- Skip / reject / escalation actions on Reminder screen  
- Removal of `DebugTrace` development logging  

## Consequences

- Confirm path works end-to-end locally with outbox evidence.  
- Postpone works locally within policy limits; sync may overwrite rescheduled times until upload exists.  
- Production readiness requires closing deferred items above before treating reminder as complete.
