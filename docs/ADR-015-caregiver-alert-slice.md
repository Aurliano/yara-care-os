# ADR-015 — Caregiver Alert Slice

Status: Proposed (in-app inbox only)  
Scope: Notification domain (draft), Integration runtime, Family App  
Related: Workflow Domain Contract (escalation / miss), Care Domain Contract (`MedicationMissed`)

## Context

The frozen Workflow contract already defines `NOTIFY_CAREGIVER` and miss
escalation. Care already interprets `ExecutionMissed` as `MEDICATION_MISSED`.
Nothing consumed `NOTIFY_CAREGIVER`, and the Family alert screen was an
honest stub (`NOTIFICATION_API_MISSING`).

SMS and push have no chosen vendor. AGENTS.md forbids inventing a frozen
Notification contract or hardcoding a provider.

## Decision

1. **Notification is a draft supporting domain**, not Frozen. This ADR plus
   `docs/domains/notification.md` are the source of truth until a later
   review freezes the contract.

2. **In-app alerts only.** `NotifyCaregiverHandler` writes a caregiver alert
   when Workflow emits `NOTIFY_CAREGIVER`. `MedicationMissed` writes a second,
   urgent alert. `GET /elders/{id}/alerts/` is the inbox the Family app
   already expected.

3. **SMS and push stay out** until a provider is chosen and stored as a
   secret. The Family UI must not pretend a phone alert was sent.

4. **Acknowledgement stays local.** Tapping «دیده‌شده» on the Family app does
   not resolve a care incident and is not written to the Backend.

5. **After `MEDICATION_MISSED`, Integration starts `INITIATE_CALL`** through
   the existing handler (priority contact). That is Care interpretation
   side-effect, not a Workflow escalation step before miss.

## Consequences

- A caregiver who opens the alert center after a missed hour sees the soft
  alert, then the missed alert, without a new vendor.
- The Frozen Workflow and Care contracts are unchanged.
- Choosing Kavenegar / SMS.ir / FCM later extends this domain; it does not
  replace the inbox.
