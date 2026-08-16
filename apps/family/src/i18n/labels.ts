import type { CareActivityStatus, CompletionState, OccurrenceStatus } from "../api/types";
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
