# Caregiver App — Backend gaps

These items are documented because the family app is a thin client and must not invent APIs.

1. **Dashboard read-model** — `GET /elders/{id}/dashboard/` does not exist. Home composes elder, care activities, prescriptions, occurrences, completions, and entitlements in `src/services/dashboard/composeDashboard.ts`.
2. **Notification inbox** — Notification domain/API is not present. Alerts UI uses `src/services/alerts/alertRepository.ts` and shows an unavailable state. Acknowledgement is local-only and never resolves a care incident.
3. **Elder device list** — Device routes are device-id scoped; `GET /elders/{id}/devices/` is missing. Hub/Pill Box summaries stay empty until that read-model exists. Battery/last-seen are shown only from `GET /devices/{id}/state/` when a device id is known.
4. **Schedule list** — `GET /schedules/` is missing. Occurrences are loaded via each care activity’s `schedule_definition_id`.
5. **MedicationRegimen** — Multi-time medication grouping is isolated in `src/services/program/medicationRegimen.ts` and not used in UI.
6. **Invitation preview** — Accept takes `invite_code` only. There is no preview of elder name/relationship before accept.
7. **Notification preferences / privacy settings** — No Backend contract. Settings toggles are disabled with explicit copy.
8. **Forgot-password / support contact** — No API. Links are non-functional with an explicit unavailable message.
9. **Caregiver workflow catalog** — Creating a first prescription requires `workflow_definition_id`. The app reuses an existing medication activity’s workflow id; it does not invent codes.
10. **Non-medication care mutations** — `MANAGE_MEDICATION` is used only for medication operations. Pause/resume/end for other activity types is not exposed from this client.
11. **Billing / plan-change UX** — `change-plan` exists and requires `MANAGE_SUBSCRIPTION`, but no payment API is present. Subscription screen is read-only.
12. **Remote compartment open** — `OPEN_COMPARTMENT` exists on Device commands. The family app never sends it.
