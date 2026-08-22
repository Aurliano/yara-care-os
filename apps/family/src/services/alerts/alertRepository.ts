/**
 * Caregiver alert inbox. Backed by GET /elders/{id}/alerts/.
 * Acknowledgement stays local and never resolves a care incident.
 */

import { getElderAlert, listElderAlerts } from "../../api/endpoints/alerts";
import { ApiError } from "../../api/errors";

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

function mapAlert(item: { id: string; title: string; body: string; severity: AlertSeverity; occurred_at: string }): CaregiverAlert {
  return {
    id: item.id,
    title: item.title,
    body: item.body,
    severity: item.severity,
    occurredAt: item.occurred_at,
  };
}

export async function loadAlertInbox(elderId: string): Promise<AlertInbox> {
  try {
    const items = await listElderAlerts(elderId);
    return { available: true, items: items.map(mapAlert) };
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return { available: false, reason: "NOTIFICATION_API_MISSING", items: [] };
    }
    throw error;
  }
}

export async function getAlertById(
  elderId: string,
  alertId: string,
): Promise<CaregiverAlert | null> {
  try {
    return mapAlert(await getElderAlert(elderId, alertId));
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 403)) {
      return null;
    }
    throw error;
  }
}
