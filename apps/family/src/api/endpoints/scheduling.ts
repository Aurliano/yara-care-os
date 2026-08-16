import { apiRequest } from "../client";
import type { Occurrence, ScheduleDefinition, ScheduleException } from "../types";

export function getSchedule(scheduleId: string): Promise<ScheduleDefinition> {
  return apiRequest(`/schedules/${scheduleId}/`);
}

export function listOccurrences(
  scheduleId: string,
  query: { type?: "upcoming" | "next" | "between"; start?: string; end?: string; limit?: number },
): Promise<Occurrence[] | Occurrence> {
  return apiRequest(`/schedules/${scheduleId}/occurrences/`, { query });
}

export function skipOccurrence(occurrenceId: string): Promise<Occurrence> {
  return apiRequest(`/occurrences/${occurrenceId}/skip/`, { method: "POST" });
}

export function createScheduleException(
  scheduleId: string,
  body: {
    original_time: string;
    exception_type: "SKIP" | "CANCEL" | "RESCHEDULE";
    replacement_time?: string;
    reason?: string;
  },
): Promise<ScheduleException> {
  return apiRequest(`/schedules/${scheduleId}/exceptions/`, { method: "POST", body });
}

export function pauseSchedule(scheduleId: string): Promise<ScheduleDefinition> {
  return apiRequest(`/schedules/${scheduleId}/pause/`, { method: "POST" });
}

export function resumeSchedule(scheduleId: string): Promise<ScheduleDefinition> {
  return apiRequest(`/schedules/${scheduleId}/resume/`, { method: "POST" });
}
