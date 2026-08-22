# Caregiver App — Backend gaps

These items are documented because the family app is a thin client and must not invent APIs.

1. **Dashboard read-model** — `GET /elders/{id}/dashboard/` does not exist. Home composes elder, care activities, prescriptions, occurrences, completions, and entitlements in `src/services/dashboard/composeDashboard.ts`.
2. **Notification inbox** — Notification domain/API is not present. Alerts stay behind the bell on every in-app screen (`/(app)/alerts`) and show an unavailable state. Acknowledgement is local-only and never resolves a care incident.
3. **Elder device list** — `GET /elders/{id}/devices/` lists assigned Hub/Pill Box devices. Home and Devices tab read that catalog.
4. **Schedule list** — `GET /schedules/` is missing. Occurrences are loaded via each care activity’s `schedule_definition_id`.
5. **MedicationRegimen** — Multi-time medication grouping is isolated in `src/services/program/medicationRegimen.ts` and not used in UI.
6. **Invitation preview** — Accept takes `invite_code` only. There is no preview of elder name/relationship before accept. Pending invitation cards never treat `invite_code` as a person name.
7. **Notification preferences / privacy settings** — No Backend contract. Settings toggles are disabled with explicit copy.
8. **Forgot-password / support contact** — No API. Links are non-functional with an explicit unavailable message.
9. **Caregiver workflow catalog** — Creating a first prescription or appointment still requires `workflow_definition_id`. The client reuses an existing activity’s id, then as a last resort `GET /workflow-definitions/by-code/wf-hub-dev-medication/` (Hub-dev seed). That code is never shown in UI. If it is missing, registration is disabled with a support message.
10. **Care writes share one permission** — Backend requires `MANAGE_MEDICATION` for both prescription create and care-activity create. The client gates both setup CTAs on that permission and does not invent a separate appointment permission.
11. **License object vs entitlements** — `GET /elders/{id}/license/` returns 404 when there is no active license. Subscription UI reads only `GET /elders/{id}/entitlements/` and never calls `/license/`.
12. **Billing / plan-change UX** — `change-plan` exists and requires `MANAGE_SUBSCRIPTION`, but no payment API is present. Subscription screen is entitlements-only.
13. **Remote compartment open** — `OPEN_COMPARTMENT` exists on Device commands. The family app never sends it.
14. **Voice message** — `channel = MESSAGE` is only a real-time session channel; there is no recorded-audio entity, upload endpoint, or storage. The call screen shows «پیام صوتی» as explicitly unavailable through `src/services/communication/voiceMessageRepository.ts`. See `docs/ADR-014-voice-message-slice.md`.
