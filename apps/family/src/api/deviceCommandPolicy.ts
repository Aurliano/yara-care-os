/** Caregiver app must never create OPEN_COMPARTMENT / CLOSE_COMPARTMENT commands. */
export const BLOCKED_CAREGIVER_COMMANDS = ["OPEN_COMPARTMENT", "CLOSE_COMPARTMENT"] as const;
