import { loadAlertInbox } from "../services/alerts/alertRepository";
import { listElderAlerts } from "../api/endpoints/alerts";
import { voiceMessageAvailability } from "../services/communication/voiceMessageRepository";
import { isDeviceConnected, loadElderDevices, normalizeConnectivity } from "../services/devices/deviceRepository";
import { MEDICATION_REGIMEN_GAP, groupMedicationTimes } from "../services/program/medicationRegimen";
import { visualKindFor } from "../services/program/activityKind";
import { BLOCKED_CAREGIVER_COMMANDS } from "../api/deviceCommandPolicy";
import { routeFromPushPayload } from "../navigation/deepLinks";
import { queryKeys } from "../api/queryKeys";
import { hasEntitlement } from "../services/licensing/entitlements";
import { listElderDevices } from "../api/endpoints/device";
import { shouldShowOnTodayProgram } from "../services/program/todayProgram";
import type { CareActivity, Occurrence } from "../api/types";

jest.mock("../api/endpoints/device", () => ({
  listElderDevices: jest.fn(),
}));
jest.mock("../api/endpoints/alerts", () => ({
  listElderAlerts: jest.fn(),
  getElderAlert: jest.fn(),
}));

const listElderDevicesMock = listElderDevices as jest.MockedFunction<typeof listElderDevices>;

describe("backend gap repositories", () => {
  it("maps caregiver alerts from Backend", async () => {
    const listElderAlertsMock = listElderAlerts as jest.MockedFunction<typeof listElderAlerts>;
    listElderAlertsMock.mockResolvedValue([
      {
        id: "alert-1",
        title: "داروی صبح هنوز مصرف نشده",
        body: "یادآوری روی هاب پاسخ داده نشده است.",
        severity: "attention",
        occurred_at: "2026-08-22T08:45:00Z",
      },
    ]);
    const inbox = await loadAlertInbox("elder-1");
    expect(inbox.available).toBe(true);
    expect(inbox.items[0]?.id).toBe("alert-1");
    expect(inbox.items[0]?.occurredAt).toBe("2026-08-22T08:45:00Z");
  });

  it("does not invent a voice message API", () => {
    const availability = voiceMessageAvailability();
    expect(availability.available).toBe(false);
    expect(availability).toEqual({ available: false, reason: "VOICE_MESSAGE_API_MISSING" });
  });

  it("maps the elder device list from Backend", async () => {
    listElderDevicesMock.mockResolvedValue([
      {
        id: "hub-1",
        kind: "HUB",
        serial_number: "TAB-1",
        operational_status: "ACTIVE",
        last_seen_at: null,
        battery_percent: 80,
        pairing_status: null,
        connectivity: "online",
        assignment_type: "OWNED",
      },
    ]);
    const catalog = await loadElderDevices("elder-1");
    expect(catalog.available).toBe(true);
    expect(catalog.items[0]?.kind).toBe("HUB");
  });

  it("treats unknown connectivity as disconnected, not assigned-active", () => {
    expect(normalizeConnectivity("ACTIVE")).toBe("unknown");
    expect(isDeviceConnected("unknown")).toBe(false);
    expect(isDeviceConnected("online")).toBe(true);
  });

  it("keeps MedicationRegimen isolated", () => {
    expect(MEDICATION_REGIMEN_GAP.available).toBe(false);
    expect(() => groupMedicationTimes(["a"])).toThrow(/MedicationRegimen/);
  });
});

describe("care visuals", () => {
  it("keeps medication distinct from other activities", () => {
    expect(visualKindFor("MEDICATION")).toBe("medication");
    expect(visualKindFor("EXERCISE")).toBe("reminder");
    expect(visualKindFor("GENERAL", "ویزیت دکتر")).toBe("appointment");
  });
});

describe("device command policy", () => {
  it("blocks remote compartment commands", () => {
    expect(BLOCKED_CAREGIVER_COMMANDS).toContain("OPEN_COMPARTMENT");
  });
});

describe("deep links", () => {
  it("routes a future push payload to an alert", () => {
    expect(routeFromPushPayload({ alert_id: "abc" })).toBe("/(app)/alerts/abc");
    expect(routeFromPushPayload({ type: "alert" })).toBe("/(app)/alerts");
  });
});

describe("query keys", () => {
  it("scopes server state by elder id", () => {
    expect(queryKeys.dashboard("e1")[1]).toBe("e1");
    expect(queryKeys.careActivities("e1")).not.toEqual(queryKeys.careActivities("e2"));
  });
});

describe("today program visibility", () => {
  const activity = (status: CareActivity["status"]): CareActivity =>
    ({
      id: "a1",
      elder_id: "e1",
      activity_type: "MEDICATION",
      display_title: "Morning",
      display_subtitle: "",
      status,
      schedule_definition_id: "s1",
      workflow_definition_id: "w1",
      confirmation_requirement: "HUB_CONFIRMATION",
      compartment_assignment_reference: "",
      aggregate_version: 1,
    }) as CareActivity;
  const occurrence = (status: Occurrence["status"]): Occurrence =>
    ({
      id: "o1",
      schedule_definition_id: "s1",
      scheduled_for: "2026-08-22T08:00:00Z",
      status,
    }) as Occurrence;

  it("hides ended programs and skipped turns from today", () => {
    expect(shouldShowOnTodayProgram(activity("ACTIVE"), occurrence("SCHEDULED"))).toBe(true);
    expect(shouldShowOnTodayProgram(activity("PAUSED"), occurrence("DUE"))).toBe(true);
    expect(shouldShowOnTodayProgram(activity("ENDED"), occurrence("SCHEDULED"))).toBe(false);
    expect(shouldShowOnTodayProgram(activity("ACTIVE"), occurrence("SKIPPED"))).toBe(false);
  });
});

describe("entitlements", () => {
  it("does not branch on plan name", () => {
    expect(hasEntitlement({ PILLBOX_SUPPORT: true }, "PILLBOX_SUPPORT")).toBe(true);
    expect(hasEntitlement({ PILLBOX_SUPPORT: false }, "PILLBOX_SUPPORT")).toBe(false);
  });
});
