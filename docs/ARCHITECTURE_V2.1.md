# Yara Hub Architecture v2.1
## Architecture Specification
### Phase II – Android Hub
### Version 2.1 — Corrected

---

# 1. Purpose

Yara Hub is **not** an Android application.

It is a dedicated elderly-care appliance built on Android.

Its responsibility is local execution of replicated domain state while remaining fully compatible with the Backend Platform.

The Backend is the source of truth.

The Hub executes replicated aggregates offline and synchronizes them back when connectivity is available.

Business ownership never moves to the Hub.

---

# 2. Design Principles

## Offline First

The Hub must continue working with no Wi-Fi, no Backend, no Cloud. Everything required for reminder execution must already exist locally.

## Backend Compatible

Every runtime behavior must produce exactly the same semantics as Backend. No alternative implementations.

## Replica Based

The Hub never owns business aggregates. It stores synchronized replicas only:

```
CareActivity Replica
WorkflowDefinition Replica
ScheduleDefinition Replica
Device Replica
Communication Replica
```

## Runtime Appliance

Hub is responsible for:

- executing replicated Scheduling state
- executing replicated Workflow state
- rendering reminders
- executing Device commands
- executing Communication sessions
- local synchronization

It is **not** responsible for:

- business decisions
- workflow definition
- schedule definition
- care interpretation
- licensing

---

# 3. Runtime Architecture

```
                     Backend
                        │
                        ▼
              Synchronization Runtime
                        │
                        ▼
              Replica Database (Room)
                        │
                        ▼
                 Runtime Kernel
                        │
                        ▼
         Scheduling Replica Runtime
                        │
                  OccurrenceDue
                        │
                        ▼
          Workflow Replica Runtime
                        │
                  Current Action
                        │
                        ▼
               Action Dispatcher
               (Coordinator, not an Engine)

       ┌──────────────┬──────────────┐
       │ Reminder UI  │  BLE Runtime │  Communication Runtime
       └──────────────┴──────────────┘
                        │
                 User Interaction
                        │
                        ▼
            ConfirmationEvidence Queue
                        │
                        ▼
              Synchronization Runtime
```

---

# 4. Ownership

| Component | Owner |
|------------|-------|
| Care meaning | Backend |
| Workflow definition | Backend |
| Schedule definition | Backend |
| Device model | Backend |
| Communication rules | Backend |
| Communication provider (API key, room/user lifecycle) | Backend |
| Workflow execution (replica) | Hub |
| Schedule execution (replica) | Hub |
| Reminder rendering | Hub |
| BLE execution | Hub |
| Offline queue | Hub |
| Synchronization client | Hub |

---

# 5. Hub Layers

```
UI → Presentation → ViewModels → UseCases → Repositories → Room + Retrofit → Platform Services → Android Runtime
```

No UI component accesses Room directly. No UI component performs network calls.

---

# 6. Replica Runtime Engines

These five components maintain ongoing state derived from replicated definitions. None of them own the definitions they execute.

## Scheduling Replica Runtime

Responsible for:

- evaluating replicated ScheduleDefinitions
- generating local Occurrences
- alarm recovery
- occurrence persistence

Never owns schedule definitions.

Consumes: ScheduleDefinition replicas
Produces: OccurrenceDue

---

## Workflow Replica Runtime

Consumes: OccurrenceDue
Creates: WorkflowExecution
Maintains: Execution State Machine
Produces: Current Action, Evidence Requests

Workflow Replica Runtime never interprets care meaning. `ExecutionConfirmed` is interpreted later by Care.

---

## Synchronization Runtime

Responsible for: replica updates, checkpoint management, delta upload, snapshot download.

Never interprets payloads. Never constructs business payloads — payload generation belongs to the owning domain runtime. Synchronization only validates, transfers and applies replicated data.

---

## Device Runtime

Responsible for: BLE, Pairing, Command execution, Command acknowledgment, Device state reporting.

---

## Communication Runtime

Responsible for: Voice sessions, Call lifecycle, Hub callbacks. No reminder logic.

The Hub must not call a communication vendor (Skyroom or any successor) and
must not contain a vendor API key. Backend owns the `CommunicationProvider`
adapter, persistent per-Elder rooms, and per-participant provider users.
The Hub only asks Backend for join credentials (`loginUrl`) and executes the
local session replica. See ADR-013.

---

## Runtime Dispatcher (Coordinator — not a Replica Engine)

**Action Dispatcher** is not one of the five Replica Runtime Engines above. Unlike them, it holds no ongoing state of its own — it only maps a Workflow Action to a runtime implementation and routes it. Treating it as an "Engine" would wrongly imply it owns independent business behavior.

Maps Workflow Actions to runtime implementations:

```
SHOW_REMINDER      → Reminder Screen
OPEN_COMPARTMENT   → Device Runtime (BLE)
INITIATE_CALL      → Communication Runtime
```

No Workflow code imports Device or Communication.

Action Dispatcher is a `RuntimeComponent` registered with the Runtime Kernel (section 16) — it does not call Device or Communication runtimes directly; all dispatch is routed through the Kernel, same as every other inter-component communication.

---

# 7. Local Database

## Replicated Tables (mirror Backend aggregates)

```
CareActivity
Prescription
WorkflowDefinition
WorkflowExecution
ScheduleDefinition
Occurrence
Device
DeviceCommand
CommunicationSession
Contact
```

## Hub-owned Tables (local operational state, not a replica of anything)

```
ReplicaState
    checkpointSequence
    checkpointToken

PendingEvidence

OutboxEntry

RuntimeState        -- persisted Runtime Kernel component states, for boot recovery
```

Checkpoint is not a separate entity — it lives inside `ReplicaState`, matching the Backend Synchronization Domain (V2).

Room is a replica-plus-local-state database. Not a cache.

---

# 8. Networking

All Backend communication goes through Retrofit.

**Authentication:** JWT

**Replica Identity:** every request identifies which Replica (this Hub) is calling, via `X-Replica-ID` / `X-Device-ID`.

**Correlation ID propagation:** every request carries `X-Correlation-ID` so a single logical operation can be traced across Hub and Backend logs. This is a transport-level tracing ID — distinct from the Event Envelope's `correlation_id` and from domain-level identifiers like `occurrence_id`; the three are related in purpose (traceability) but are not the same field and must not be conflated.

Headers:

```
Authorization
X-Correlation-ID
X-Replica-ID
X-Device-ID
```

No direct OkHttp usage outside Networking layer.

---

# 9. Background Runtime

```
BootReceiver → WorkManager → Integration Runtime → Scheduling Runtime → Workflow Runtime
```

AlarmManager is only used as a wake-up trigger. Business logic never lives inside BroadcastReceivers.

---

# 10. Integration Runtime

This is the component that turns the Hub from an Android app into a runtime appliance — it deserves as much weight here as it has in the actual system.

Runs periodically (and on wake-up triggers from AlarmManager).

**Responsibilities:**

- Consume local events (OccurrenceDue, DeviceCommand acknowledgments, CommunicationSession outcomes)
- Dispatch workflow actions (drive Action Dispatcher for each pending Current Action)
- Route confirmations (take ConfirmationEvidence from UI/BLE/Communication and feed it to Workflow Replica Runtime)
- Process due Occurrences (poll Scheduling Replica Runtime, hand results to Workflow Replica Runtime)
- Handle Workflow timeouts (drive escalation steps when a WorkflowExecution's confirmation window lapses)
- Start synchronization (trigger a Synchronization Session when connectivity is available or a batch of PendingEvidence accumulates)
- Drive Device Runtime (issue queued DeviceCommands, collect acknowledgments)
- Drive Communication Runtime (issue queued call/session requests, collect outcomes)

Integration Runtime is itself a `RuntimeComponent` — it does not bypass the Runtime Kernel to reach the engines above; it orchestrates them through it.

---

# 11. UI Philosophy

UI reflects runtime state. UI never creates business state.

Wrong: `Medication.isCompleted = true`
Correct: `WorkflowExecution.state == CONFIRMED`

---

# 12. Reminder Flow

```
OccurrenceDue
↓
Workflow Replica Runtime
↓
SHOW_REMINDER
↓
Reminder Screen
↓
User Confirmation
↓
ConfirmationEvidence
↓
ExecutionConfirmed   (Hub-local — immediate, works offline)
↓
Synchronization
↓
ExecutionConfirmed   (Backend reconciliation)
↓
Care Interpretation
↓
MedicationTaken
```

Confirmation is decided **locally and immediately** by the Workflow Replica Runtime — the Hub does not wait for Backend connectivity to know an activity was confirmed (required for local escalation/reminder suppression to work offline). Synchronization only carries this already-decided state to the Backend; it is not a prerequisite for the confirmation itself.

Hub never produces `MedicationTaken`. That interpretation belongs exclusively to Care, on the Backend.

---

# 13. BLE Flow

```
Workflow Replica Runtime
↓
DeviceCommand
↓
Device Runtime
↓
BLE
↓
ESP32
↓
Compartment Event
↓
Device Runtime
↓
Evidence
↓
Workflow Replica Runtime
```

Device Runtime mediates in both directions — BLE never produces Evidence directly; it produces a hardware fact that Device Runtime turns into Evidence.

---

# 14. Offline Flow

```
OccurrenceDue
↓
WorkflowExecution
↓
ConfirmationEvidence
↓
PendingEvidence
↓
Outbox
↓
Synchronization Runtime
↓
Synchronization Session
↓
Backend
```

---

# 15. Replica Boundary

Every replicated aggregate originates from the Backend:

```
CareActivity, Prescription, WorkflowDefinition, WorkflowExecution,
ScheduleDefinition, Occurrence, Device, DeviceCommand, CommunicationSession
```

The Hub may persist, execute and synchronize these replicas. The Hub never becomes their business owner.

---

# 16. Runtime Kernel

All runtime components share the same lifecycle:

```
CREATED → INITIALIZED → STARTING → RUNNING → PAUSED → STOPPING → STOPPED → FAILED
```

Rather than freezing concrete classes, the Runtime Kernel is defined by the capabilities it must provide:

- **Component registration** — every engine (section 6) and the Integration Runtime register themselves with the Kernel at startup.
- **Lifecycle management** — the Kernel drives each component through the lifecycle above and persists enough state (`RuntimeState`, section 7) to recover after a reboot.
- **Component communication** — all inter-component calls (e.g., Action Dispatcher → Device Runtime) are routed through the Kernel; components never call each other directly.
- **Health monitoring** — the Kernel can query the current state of any registered component.

The concrete class design (manager/registry/component interfaces, etc.) is an implementation decision for Sprint II-A, not something this document freezes.

---

# 17. Project Modules (illustrative, not authoritative)

The architectural contract is the **layering**, not any specific Gradle module name:

```
UI Layer
Runtime Layer   (Kernel, Scheduling, Workflow, Dispatcher, Synchronization, Device, Communication)
Persistence Layer
Networking Layer
```

One reasonable way to map this to Gradle modules — subject to change without touching this document:

```
:app  :core  :common  :data  :network  :database  :sync
:runtime (:kernel :scheduling :workflow :synchronization :device :communication)
:features-home  :features-reminder  :features-settings
```

If the module structure changes, this document does not need to change — only the layering above is part of the architecture.

---

# 18. Forbidden Patterns

- Business logic inside Activities or Composables
- Direct Room access from UI
- Reminder decisions in UI
- Medication CRUD on Hub
- Duplicate Care or Workflow business rules
- BLE logic inside UI
- Synchronization payload construction outside owning domains
- Local models that diverge from Backend terminology
- Runtime components calling each other directly instead of through the Runtime Kernel
- Treating a stateless coordinator (e.g., Action Dispatcher) as if it were a stateful Replica Engine
- Hub or Family App calling Skyroom (or any communication vendor) directly
- Storing a communication-vendor API key on the Hub or in client apps

---

# 19. Sprint II Goal

By the end of Phase II, the Hub must:

- Boot and recover after restart.
- Operate without network connectivity.
- Execute local scheduling and workflow.
- Drive reminders, BLE, and communication.
- Queue evidence and synchronize when connectivity returns.
- Remain semantically identical to the Backend Platform.

---

## Architecture Vision

> **The Backend owns business semantics and decides what should happen. The Hub executes replicated domain state locally, survives offline operation, and synchronizes results back without becoming the owner of business meaning.**
