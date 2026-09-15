import { composeDashboard } from "../services/dashboard/composeDashboard";
import { getElder } from "../api/endpoints/identity";
import { listCareActivities, listCompletions, listPrescriptions } from "../api/endpoints/care";
import { getEntitlements } from "../api/endpoints/licensing";
import { listOccurrences } from "../api/endpoints/scheduling";
import { loadElderDevices } from "../services/devices/deviceRepository";
import type { CareActivity, Elder, Occurrence } from "../api/types";

jest.mock("../api/endpoints/identity", () => ({
  getElder: jest.fn(),
}));
jest.mock("../api/endpoints/care", () => ({
  listCareActivities: jest.fn(),
  listCompletions: jest.fn(),
  listPrescriptions: jest.fn(),
}));
jest.mock("../api/endpoints/licensing", () => ({
  getEntitlements: jest.fn(),
}));
jest.mock("../api/endpoints/scheduling", () => ({
  listOccurrences: jest.fn(),
}));
jest.mock("../services/devices/deviceRepository", () => ({
  loadElderDevices: jest.fn(),
}));

describe("composeDashboard", () => {
  const mockElder: Elder = {
    id: "elder-1",
    full_name: "مادر بزرگ",
    birth_date: "1950-01-01",
    status: "ACTIVE",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };

  const mockDevices = {
    devices: [],
    hub: null,
    pillbox: null,
    smartwatch: null,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (getElder as jest.Mock).mockResolvedValue(mockElder);
    (getEntitlements as jest.Mock).mockResolvedValue({ entitlements: {} });
    (loadElderDevices as jest.Mock).mockResolvedValue(mockDevices);
    (listPrescriptions as jest.Mock).mockResolvedValue([]);
    (listCompletions as jest.Mock).mockResolvedValue([]);
  });

  it("filters out SKIPPED occurrences and does not trigger false attention tone", async () => {
    const activeActivity: CareActivity = {
      id: "act-1",
      elder_id: "elder-1",
      activity_type: "MEDICATION",
      display_title: "داروی قلب",
      display_subtitle: "صبح",
      display_icon: "med",
      status: "ACTIVE",
      schedule_definition_id: "sched-1",
      workflow_definition_id: "wf-1",
      confirmation_requirement: {},
      compartment_assignment_reference: "",
      aggregate_version: 1,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };

    const skippedOccurrence: Occurrence = {
      id: "occ-skipped",
      schedule_definition: "sched-1",
      scheduled_for: "2026-09-09T08:00:00Z",
      status: "SKIPPED",
      created_at: "2026-09-09T08:00:00Z",
    };

    (listCareActivities as jest.Mock).mockResolvedValue([activeActivity]);
    (listOccurrences as jest.Mock).mockResolvedValue([skippedOccurrence]);

    const dashboard = await composeDashboard("elder-1");

    expect(dashboard.today).toHaveLength(0);
    expect(dashboard.tone).toBe("calm");
    expect(dashboard.topAction).toBeNull();
  });

  it("filters out CANCELLED occurrences and occurrences from ENDED activities", async () => {
    const endedActivity: CareActivity = {
      id: "act-ended",
      elder_id: "elder-1",
      activity_type: "MEDICATION",
      display_title: "داروی قطع شده",
      display_subtitle: "",
      display_icon: "med",
      status: "ENDED",
      schedule_definition_id: "sched-ended",
      workflow_definition_id: "wf-1",
      confirmation_requirement: {},
      compartment_assignment_reference: "",
      aggregate_version: 1,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };

    const dueOccurrence: Occurrence = {
      id: "occ-due",
      schedule_definition: "sched-ended",
      scheduled_for: "2026-09-09T08:00:00Z",
      status: "DUE",
      created_at: "2026-09-09T08:00:00Z",
    };

    (listCareActivities as jest.Mock).mockResolvedValue([endedActivity]);
    (listOccurrences as jest.Mock).mockResolvedValue([dueOccurrence]);

    const dashboard = await composeDashboard("elder-1");

    expect(dashboard.today).toHaveLength(0);
    expect(dashboard.tone).toBe("calm");
  });

  it("includes valid ACTIVE and DUE occurrences and triggers attention tone", async () => {
    const activeActivity: CareActivity = {
      id: "act-active",
      elder_id: "elder-1",
      activity_type: "MEDICATION",
      display_title: "داروی فعال",
      display_subtitle: "",
      display_icon: "med",
      status: "ACTIVE",
      schedule_definition_id: "sched-active",
      workflow_definition_id: "wf-1",
      confirmation_requirement: {},
      compartment_assignment_reference: "",
      aggregate_version: 1,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };

    const dueOccurrence: Occurrence = {
      id: "occ-due",
      schedule_definition: "sched-active",
      scheduled_for: "2026-09-09T08:00:00Z",
      status: "DUE",
      created_at: "2026-09-09T08:00:00Z",
    };

    (listCareActivities as jest.Mock).mockResolvedValue([activeActivity]);
    (listOccurrences as jest.Mock).mockResolvedValue([dueOccurrence]);

    const dashboard = await composeDashboard("elder-1");

    expect(dashboard.today).toHaveLength(1);
    expect(dashboard.today[0].activity.id).toBe("act-active");
    expect(dashboard.tone).toBe("attention");
    expect(dashboard.topAction?.occurrence.id).toBe("occ-due");
  });
});
