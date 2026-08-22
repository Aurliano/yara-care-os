import type { QueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../api/queryKeys";
import type { CareActivity, CareActivityStatus, Occurrence, OccurrenceStatus } from "../../api/types";

const LISTED_ACTIVITY_STATUSES: readonly CareActivityStatus[] = ["ACTIVE", "PAUSED"];
const HIDDEN_OCCURRENCE_STATUSES: readonly OccurrenceStatus[] = ["SKIPPED", "CANCELLED"];

export function isListedOnTodayProgram(status: CareActivityStatus | string): boolean {
  return (LISTED_ACTIVITY_STATUSES as readonly string[]).includes(status);
}

export function isVisibleTodayOccurrence(status: OccurrenceStatus | string): boolean {
  return !(HIDDEN_OCCURRENCE_STATUSES as readonly string[]).includes(status);
}

export function shouldShowOnTodayProgram(activity: CareActivity, occurrence: Occurrence): boolean {
  return isListedOnTodayProgram(activity.status) && isVisibleTodayOccurrence(occurrence.status);
}

export function invalidateProgramQueries(
  queryClient: QueryClient,
  elderId: string | null | undefined,
  activityId?: string,
): void {
  if (elderId) {
    void queryClient.invalidateQueries({ queryKey: queryKeys.careActivities(elderId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.prescriptions(elderId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(elderId) });
  }
  if (activityId) {
    void queryClient.invalidateQueries({ queryKey: ["care-activity", activityId] });
  }
}
