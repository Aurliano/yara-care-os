/**
 * Notification Domain is not implemented in Backend.
 * All alert UI must go through this repository so we never invent an inbox API.
 */

export type AlertSeverity = "urgent" | "attention" | "reminder" | "informational";

export type CaregiverAlert = {
  id: string;
  title: string;
  body: string;
  severity: AlertSeverity;
  occurredAt: string;
};

export type AlertInbox =
  | { available: false; reason: "NOTIFICATION_API_MISSING"; items: [] }
  | { available: true; items: CaregiverAlert[] };

export async function loadAlertInbox(_elderId: string): Promise<AlertInbox> {
  return { available: false, reason: "NOTIFICATION_API_MISSING", items: [] };
}

export async function getAlertById(
  _elderId: string,
  _alertId: string,
): Promise<CaregiverAlert | null> {
  return null;
}
