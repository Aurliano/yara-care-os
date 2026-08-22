# Yara — Notification Domain Contract

**Domain:** Notification  
**Classification:** Supporting Domain  
**Status:** Draft  
**Version:** 0.1

---

## 1. Purpose

Notification owns **caregiver-visible alerts** that are not Care completions
and not Communication sessions.

This domain answers:

> What should a caregiver see in the in-app inbox when a reminder is late
> or a dose is missed?

It does **not** send SMS or push until a later ADR names a provider.

---

## 2. Ubiquitous Language

### Caregiver Alert

A durable inbox item for one Elder:

- title
- body
- severity (`urgent` | `attention` | `reminder` | `informational`)
- occurred_at

Notification does not interpret whether a dose was taken. Care owns that.

### Delivery Channel

MVP channel is `IN_APP` only. SMS and push are out of scope.

---

## 3. Aggregates

### CaregiverAlert

| Field | Notes |
| --- | --- |
| id | Stable UUID |
| elder_id | Elder the alert is about |
| title | Short Persian-capable text |
| body | One-sentence explanation |
| severity | `urgent` / `attention` / `reminder` / `informational` |
| occurred_at | When the source fact happened |
| source_type | Opaque producer tag (`NOTIFY_CAREGIVER`, `MEDICATION_MISSED`) |
| source_reference | Idempotency key (execution id or completion id) |

---

## 4. Commands

- `RecordCaregiverAlert` — create or return the existing row for the same
  `(source_type, source_reference)`.

## 5. Queries

- `ListElderAlerts`
- `GetAlert`

---

## 6. API (draft)

- `GET /elders/{elder_id}/alerts/`
- `GET /elders/{elder_id}/alerts/{alert_id}/`

Requires an authenticated membership and `VIEW_ELDER_STATUS`.

Response fields: `id`, `title`, `body`, `severity`, `occurred_at`.

---

## 7. Boundaries

Notification:

- may reference an Elder
- must not import Care, Workflow, Scheduling, Device, or Communication models
- must not choose an SMS or push vendor

Integration records alerts from `EscalationTriggered` (`NOTIFY_CAREGIVER`)
and `MedicationMissed`.

---

## 8. Out of scope

- SMS / IVR / email
- Push tokens and device registration
- Resolving or closing a care incident from the inbox
- Elder-facing notifications (those stay on the Hub)
