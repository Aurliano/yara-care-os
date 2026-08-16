import { apiRequest } from "../client";
import type { CareActivity, CareCompletion, Prescription } from "../types";

export function listCareActivities(elderId: string): Promise<CareActivity[]> {
  return apiRequest(`/elders/${elderId}/care-activities/`);
}

export function getCareActivity(activityId: string): Promise<CareActivity> {
  return apiRequest(`/care-activities/${activityId}/`);
}

export function pauseCareActivity(activityId: string): Promise<CareActivity> {
  return apiRequest(`/care-activities/${activityId}/pause/`, { method: "POST" });
}

export function resumeCareActivity(activityId: string): Promise<CareActivity> {
  return apiRequest(`/care-activities/${activityId}/resume/`, { method: "POST" });
}

export function endCareActivity(activityId: string): Promise<CareActivity> {
  return apiRequest(`/care-activities/${activityId}/end/`, { method: "POST" });
}

export function listCompletions(activityId: string): Promise<CareCompletion[]> {
  return apiRequest(`/care-activities/${activityId}/completions/`);
}

export function listPrescriptions(elderId: string): Promise<Prescription[]> {
  return apiRequest(`/elders/${elderId}/prescriptions/`);
}

export function createPrescription(
  elderId: string,
  body: {
    workflow_definition_id: string;
    recurrence_definition: Record<string, unknown>;
    timezone_name: string;
    start_at: string;
    display_title: string;
    display_subtitle?: string;
    medication_reference: string;
    dosage_information: string;
    elder_friendly_description: string;
    personalized_description?: string;
  },
): Promise<Prescription> {
  return apiRequest(`/elders/${elderId}/prescriptions/`, { method: "POST", body });
}

export function createCareActivity(
  elderId: string,
  body: {
    activity_type: string;
    workflow_definition_id: string;
    recurrence_definition: Record<string, unknown>;
    timezone_name: string;
    start_at: string;
    display_title: string;
    display_subtitle?: string;
  },
): Promise<CareActivity> {
  return apiRequest(`/elders/${elderId}/care-activities/`, { method: "POST", body });
}
