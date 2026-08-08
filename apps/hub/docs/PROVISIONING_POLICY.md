# Hub Provisioning Policy

Status: Approved (Sprint II-E Phase A)

## Principle

**Backend is the sole authority for device and replica identity.**  
The Hub never fabricates `device_id`, `replica_id`, or provisioning state.

## Device Identity

| Rule | Description |
|------|-------------|
| **Identity key** | `serial_number` (Hub sends `ANDROID_ID`) |
| **Registration** | Idempotent — repeated register with the same serial returns the same `device_id` and `replica_identifier` |
| **Reinstall** | Does **not** create a new replica (same hardware → same serial → same identity) |
| **Factory reset** | Does **not** create a new replica (serial is stable on the same appliance) |
| **Revoke** | Only `POST /hub/provision/revoke/` causes a **new** `replica_identifier` on next register |

## State Machine (Hub)

```
UNPROVISIONED → REGISTERING → REGISTERED → AUTHENTICATING → READY
```

Transitions are driven only by backend responses.

## Runtime Gate (Defense in Depth)

**No Runtime, Synchronization, Alarm Recovery, or Integration Cycle may run until `ProvisioningState == READY`.**

Gates are enforced at:

1. `YaraApplication` — waits for READY before `Runtime.recover()` and scheduler registration
2. `HubRuntimeOrchestrator` — `recover()` / `runCycle()` no-op when not READY
3. `IntegrationRuntimeWorker` — returns `Result.success()` immediately when not READY
4. `ConnectivitySyncTrigger` — does not enqueue worker when not READY
5. `RunSynchronizationCycleUseCase` / `SynchronizationClient` — skips sync without HTTP calls

Strict check requires: `READY` state + valid `device_id` + `replica_id` + JWT.

## API Endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/hub/provision/register/` | Public |
| POST | `/api/v1/hub/provision/authenticate/` | Public |
| GET | `/api/v1/hub/provision/status/` | Public (device_id) |
| POST | `/api/v1/hub/provision/revoke/` | JWT required |

## Conflict Policy (409)

**Not used.** For Yara Hub appliances, same hardware always maps to the same identity.  
Use `revoke` when intentionally decommissioning a device.
