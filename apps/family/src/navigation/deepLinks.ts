import { loadAlertInbox } from "../services/alerts/alertRepository";

/** Future push payload → in-app route. Keep payload keys aligned with a future Notification contract. */
export function routeFromPushPayload(payload: Record<string, unknown>): string {
  const alertId = payload.alert_id ?? payload.notification_id;
  if (typeof alertId === "string" && alertId.length > 0) {
    return `/(app)/alerts/${alertId}`;
  }
  if (payload.type === "alert") {
    return "/(app)/alerts";
  }
  return "/(app)/(tabs)";
}

export async function isAlertInboxReady(elderId: string): Promise<boolean> {
  const inbox = await loadAlertInbox(elderId);
  return inbox.available;
}
