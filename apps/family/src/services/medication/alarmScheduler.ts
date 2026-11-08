import { NativeModules, Platform } from "react-native";
import type { CareActivity, Occurrence, Prescription } from "../../api/types";

const { MedicationAlarmModule } = NativeModules;

export type AlarmScheduleItem = {
  id: string;
  title: string;
  dosage: string;
  timeLabel: string;
  timestampMs: number;
};

export type ProgramAlarmItem = {
  activity: CareActivity;
  occurrence: Occurrence;
  prescription?: Prescription;
};

/**
 * Schedules a native exact alarm with full-screen wakeup on Android.
 */
export async function scheduleMedicationAlarm(item: AlarmScheduleItem): Promise<boolean> {
  if (Platform.OS !== "android" || !MedicationAlarmModule) {
    return false;
  }
  try {
    const success = await MedicationAlarmModule.scheduleAlarm(
      item.id,
      item.title,
      item.dosage || "",
      item.timeLabel,
      item.timestampMs
    );
    return Boolean(success);
  } catch (err) {
    console.warn("[MedicationAlarm] Failed to schedule alarm:", err);
    return false;
  }
}

/**
 * Cancels a previously scheduled alarm by its unique id.
 */
export async function cancelMedicationAlarm(id: string): Promise<boolean> {
  if (Platform.OS !== "android" || !MedicationAlarmModule) {
    return false;
  }
  try {
    await MedicationAlarmModule.cancelAlarm(id);
    return true;
  } catch (err) {
    console.warn("[MedicationAlarm] Failed to cancel alarm:", err);
    return false;
  }
}

/**
 * Snoozes an alarm for the given minutes (default 10 minutes).
 */
export async function snoozeMedicationAlarm(
  item: Omit<AlarmScheduleItem, "timestampMs">,
  minutes = 10
): Promise<boolean> {
  const snoozeTime = Date.now() + minutes * 60 * 1000;
  return scheduleMedicationAlarm({
    ...item,
    id: `${item.id}-snooze-${Date.now()}`,
    timeLabel: `${minutes} دقیقه بعد`,
    timestampMs: snoozeTime,
  });
}

/**
 * Schedules alarms for all program occurrences that are upcoming.
 */
export async function syncProgramAlarms(items: ProgramAlarmItem[]): Promise<number> {
  if (Platform.OS !== "android" || !MedicationAlarmModule) {
    return 0;
  }

  const now = Date.now();
  let count = 0;

  for (const item of items) {
    if (item.occurrence.status === "CANCELLED" || item.occurrence.status === "SKIPPED") {
      continue;
    }
    const occurrenceTime = new Date(item.occurrence.scheduled_for).getTime();
    if (occurrenceTime > now + 15 * 1000) {
      const timeDate = new Date(occurrenceTime);
      const h = String(timeDate.getHours()).padStart(2, "0");
      const m = String(timeDate.getMinutes()).padStart(2, "0");
      const ok = await scheduleMedicationAlarm({
        id: item.occurrence.id,
        title: item.activity.display_title || "داروی تجویزی",
        dosage: item.prescription?.dosage_information || item.activity.display_subtitle || "",
        timeLabel: `${h}:${m}`,
        timestampMs: occurrenceTime,
      });
      if (ok) count++;
    }
  }

  return count;
}
