import { endOfLocalDay, startOfLocalDay } from "../../i18n/dates";
import { listCareActivities, listCompletions, listPrescriptions } from "../../api/endpoints/care";
import { getElder } from "../../api/endpoints/identity";
import { getEntitlements } from "../../api/endpoints/licensing";
import { listOccurrences } from "../../api/endpoints/scheduling";
import type {
  CareActivity,
  CareCompletion,
  Elder,
  EntitlementMap,
  Occurrence,
  Prescription,
} from "../../api/types";
import { loadElderDevices, type ElderDeviceCatalog } from "../devices/deviceRepository";

export type DashboardTone = "calm" | "attention" | "urgent" | "unknown";

export type DashboardFreshness =
  | { kind: "live"; updatedAt: string }
  | { kind: "stale"; updatedAt: string }
  | { kind: "unavailable" };

export type TodayItem = {
  activity: CareActivity;
  occurrence: Occurrence;
  prescription?: Prescription;
  completion?: CareCompletion;
};

export type DashboardModel = {
  elder: Elder;
  tone: DashboardTone;
  freshness: DashboardFreshness;
  topAction: TodayItem | null;
  today: TodayItem[];
  devices: ElderDeviceCatalog;
  entitlements: EntitlementMap;
  setupRequired: boolean;
};

function isMissed(state: CareCompletion["completion_state"] | undefined): boolean {
  return state === "MEDICATION_MISSED" || state === "CARE_ACTIVITY_MISSED";
}

export async function composeDashboard(elderId: string): Promise<DashboardModel> {
  const [elder, activities, prescriptions, entitlements, devices] = await Promise.all([
    getElder(elderId),
    listCareActivities(elderId),
    listPrescriptions(elderId),
    getEntitlements(elderId).catch(() => ({ entitlements: {} as EntitlementMap })),
    loadElderDevices(elderId),
  ]);

  const start = startOfLocalDay().toISOString();
  const end = endOfLocalDay().toISOString();
  const prescriptionByActivity = new Map(prescriptions.map((item) => [item.care_activity_id, item]));

  const today: TodayItem[] = [];
  const completions: CareCompletion[] = [];

  await Promise.all(
    activities.map(async (activity) => {
      const [occResult, history] = await Promise.all([
        listOccurrences(activity.schedule_definition_id, { type: "between", start, end }).catch(
          () => [] as Occurrence[],
        ),
        listCompletions(activity.id).catch(() => [] as CareCompletion[]),
      ]);
      completions.push(...history);
      const occurrences = Array.isArray(occResult) ? occResult : occResult ? [occResult] : [];
      for (const occurrence of occurrences) {
        today.push({
          activity,
          occurrence,
          prescription: prescriptionByActivity.get(activity.id),
          completion: history.find((item) => item.occurrence_id === occurrence.id),
        });
      }
    }),
  );

  today.sort(
    (a, b) =>
      new Date(a.occurrence.scheduled_for).getTime() - new Date(b.occurrence.scheduled_for).getTime(),
  );

  const missed = today.filter((item) => isMissed(item.completion?.completion_state));
  const dueUnconfirmed = today.filter(
    (item) => item.occurrence.status === "DUE" && !item.completion,
  );
  let tone: DashboardTone = "calm";
  if (missed.length > 0) {
    tone = "urgent";
  } else if (dueUnconfirmed.length > 0) {
    tone = "attention";
  }

  const timestamps = [
    elder.updated_at,
    ...activities.map((item) => item.updated_at),
    ...today.map((item) => item.occurrence.scheduled_for),
  ];
  const updatedAt = timestamps.sort().at(-1) ?? new Date().toISOString();

  return {
    elder,
    tone,
    freshness: { kind: "live", updatedAt },
    topAction: missed[0] ?? dueUnconfirmed[0] ?? null,
    today,
    devices,
    entitlements: entitlements.entitlements,
    setupRequired: activities.length === 0,
  };
}

export { hasEntitlement } from "../licensing/entitlements";
