export const queryKeys = {
  me: ["me"] as const,
  elders: ["elders"] as const,
  elder: (elderId: string) => ["elder", elderId] as const,
  permissions: (elderId: string) => ["elder", elderId, "permissions"] as const,
  members: (elderId: string) => ["elder", elderId, "members"] as const,
  invitations: (elderId: string) => ["elder", elderId, "invitations"] as const,
  emergencyRecipients: (elderId: string) => ["elder", elderId, "emergency-recipients"] as const,
  careActivities: (elderId: string) => ["elder", elderId, "care-activities"] as const,
  prescriptions: (elderId: string) => ["elder", elderId, "prescriptions"] as const,
  completions: (activityId: string) => ["care-activity", activityId, "completions"] as const,
  occurrences: (scheduleId: string, range: string) =>
    ["schedule", scheduleId, "occurrences", range] as const,
  entitlements: (elderId: string) => ["elder", elderId, "entitlements"] as const,
  contacts: (elderId: string) => ["elder", elderId, "contacts"] as const,
  dashboard: (elderId: string) => ["elder", elderId, "dashboard"] as const,
  devices: (elderId: string) => ["elder", elderId, "devices"] as const,
  deviceState: (deviceId: string) => ["device", deviceId, "state"] as const,
  pairings: (deviceId: string) => ["device", deviceId, "pairings"] as const,
  alerts: (elderId: string) => ["elder", elderId, "alerts"] as const,
};

export const elderScopePrefix = (elderId: string) => ["elder", elderId];
