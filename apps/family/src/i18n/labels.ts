import type { CareActivityStatus, CompletionState, EntitlementKey, OccurrenceStatus } from "../api/types";
import { fa as t } from "./fa";

export function careActivityStatusLabel(status: CareActivityStatus | string): string {
  switch (status) {
    case "ACTIVE":
      return t.statusActive;
    case "PAUSED":
      return t.statusPaused;
    case "ENDED":
      return t.statusEnded;
    case "CANCELLED":
      return t.statusCancelled;
    default:
      return t.unknownValue;
  }
}

export function completionStateLabel(state: CompletionState | string): string {
  switch (state) {
    case "MEDICATION_TAKEN":
      return t.completionTaken;
    case "MEDICATION_MISSED":
      return t.completionMissed;
    case "CARE_ACTIVITY_COMPLETED":
      return t.completionDone;
    case "CARE_ACTIVITY_MISSED":
      return t.completionMissed;
    case "CARE_ACTIVITY_CANCELLED":
      return t.completionCancelled;
    case "CARE_ACTIVITY_FAILED":
      return t.completionFailed;
    default:
      return t.unknownValue;
  }
}

export function occurrenceStatusLabel(status: OccurrenceStatus | string): string {
  switch (status) {
    case "SCHEDULED":
      return t.occurrenceScheduled;
    case "DUE":
      return t.occurrenceDue;
    case "CANCELLED":
      return t.occurrenceCancelled;
    case "SKIPPED":
      return t.occurrenceSkipped;
    default:
      return t.unknownValue;
  }
}

export function entitlementLabel(key: EntitlementKey | string): string {
  switch (key) {
    case "MAX_CAREGIVERS":
      return t.entitlementMaxCaregivers;
    case "MAX_HUBS":
      return t.entitlementMaxHubs;
    case "MAX_PILLBOXES":
      return t.entitlementMaxPillboxes;
    case "PILLBOX_SUPPORT":
      return t.entitlementPillbox;
    case "SENSOR_SUPPORT":
      return t.entitlementSensor;
    case "VIDEO_CALL":
      return t.entitlementVideoCall;
    default:
      return t.entitlementOther;
  }
}
