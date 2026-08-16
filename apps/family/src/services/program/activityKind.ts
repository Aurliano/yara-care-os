import type { CareActivityType } from "../../api/types";

export type VisualKind = "medication" | "appointment" | "reminder";

/**
 * Backend activity types: MEDICATION | EXERCISE | DAILY_CHECK_IN | GENERAL.
 * Appointment is not a domain type; GENERAL/DAILY_CHECK_IN are shown as appointment-like
 * only when display copy is appointment-related. Exercise/general otherwise use reminder styling.
 */
export function visualKindFor(activityType: CareActivityType, title = ""): VisualKind {
  if (activityType === "MEDICATION") {
    return "medication";
  }
  if (/ویزیت|دکتر|نوبت|کلینیک/.test(title) || activityType === "DAILY_CHECK_IN") {
    return "appointment";
  }
  return "reminder";
}

export const KIND_ACCENT = {
  medication: "medication",
  appointment: "info",
  reminder: "none",
} as const;
