import { loadAlertInbox } from "../services/alerts/alertRepository";
import { loadElderDevices } from "../services/devices/deviceRepository";
import { MEDICATION_REGIMEN_GAP, groupMedicationTimes } from "../services/program/medicationRegimen";
import { visualKindFor } from "../services/program/activityKind";
import { BLOCKED_CAREGIVER_COMMANDS } from "../api/deviceCommandPolicy";
import { routeFromPushPayload } from "../navigation/deepLinks";
import { queryKeys } from "../api/queryKeys";
import { hasEntitlement } from "../services/licensing/entitlements";

describe("backend gap repositories", () => {
  it("does not invent a notification inbox", async () => {
    const inbox = await loadAlertInbox("elder-1");
    expect(inbox.available).toBe(false);
    expect(inbox.items).toEqual([]);
  });

  it("does not invent an elder device list", async () => {
    const catalog = await loadElderDevices("elder-1");
    expect(catalog.available).toBe(false);
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

describe("entitlements", () => {
  it("does not branch on plan name", () => {
    expect(hasEntitlement({ PILLBOX_SUPPORT: true }, "PILLBOX_SUPPORT")).toBe(true);
    expect(hasEntitlement({ PILLBOX_SUPPORT: false }, "PILLBOX_SUPPORT")).toBe(false);
  });
});
