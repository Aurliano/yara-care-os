/**
 * Isolated future capability. Do not use in UI until Backend MedicationRegimen exists.
 * Current care model is one CareActivity + one ScheduleDefinition per prescription.
 */
export const MEDICATION_REGIMEN_GAP = {
  available: false,
  reason: "MEDICATION_REGIMEN_MISSING",
} as const;

export function groupMedicationTimes(_activityIds: string[]): never {
  throw new Error("MedicationRegimen is not available on the Backend.");
}
