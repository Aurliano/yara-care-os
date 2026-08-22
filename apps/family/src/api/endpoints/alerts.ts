import { apiRequest } from "../client";
import type { CaregiverAlert } from "../types";

export function listElderAlerts(elderId: string): Promise<CaregiverAlert[]> {
  return apiRequest(`/elders/${elderId}/alerts/`);
}

export function getElderAlert(elderId: string, alertId: string): Promise<CaregiverAlert> {
  return apiRequest(`/elders/${elderId}/alerts/${alertId}/`);
}
