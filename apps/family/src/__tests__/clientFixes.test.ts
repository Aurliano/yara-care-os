import * as licensing from "../api/endpoints/licensing";
import { APP_TABS } from "../navigation/tabs";
import { entitlementLabel } from "../i18n/labels";
import { routeFromPushPayload } from "../navigation/deepLinks";
import {
  invitationShareMessage,
  pendingInvitationTitle,
  usesInviteCodeAsName,
} from "../services/family/invitationDisplay";
import { combineTehranDateTime, onceRecurrence } from "../services/program/onceSchedule";
import { resolveCareWorkflowDefinitionId } from "../services/program/workflowDefinition";
import { listCareActivities, listPrescriptions } from "../api/endpoints/care";
import { getWorkflowDefinitionByCode } from "../api/endpoints/workflow";
import { ApiError } from "../api/errors";

jest.mock("../api/endpoints/care", () => ({
  listCareActivities: jest.fn(),
  listPrescriptions: jest.fn(),
}));
jest.mock("../api/endpoints/workflow", () => ({
  getWorkflowDefinitionByCode: jest.fn(),
}));

describe("subscription client contract", () => {
  it("does not expose GET /license/", () => {
    expect("getElderLicense" in licensing).toBe(false);
    expect(typeof licensing.getEntitlements).toBe("function");
  });
});

describe("invitation display", () => {
  it("never uses the invite code as the pending card title", () => {
    const code = "cFCHTbfABC";
    expect(pendingInvitationTitle()).toBe("دعوت در انتظار پذیرش");
    expect(usesInviteCodeAsName(pendingInvitationTitle(), code)).toBe(false);
  });

  it("keeps the invite code latin in the share message", () => {
    const code = "cFCHTbfABC";
    const message = invitationShareMessage("مراقب", code);
    expect(message).toContain(code);
    expect(message).toContain("مراقب");
  });
});

describe("one-time schedule", () => {
  it("builds a Tehran once slot from date and time", () => {
    expect(combineTehranDateTime("2026-08-16", "08:30")).toBe("2026-08-16T08:30:00+03:30");
    expect(onceRecurrence()).toEqual({ type: "once" });
  });

  it("rejects invalid date or time", () => {
    expect(combineTehranDateTime("16/08/2026", "08:00")).toBeNull();
    expect(combineTehranDateTime("2026-08-16", "25:00")).toBeNull();
  });

  it("accepts Persian digits for a valid gregorian date", () => {
    expect(combineTehranDateTime("۲۰۲۶-۰۸-۱۶", "۸:۰۵")).toBe("2026-08-16T08:05:00+03:30");
  });
});

describe("workflow definition resolver", () => {
  const activities = listCareActivities as jest.MockedFunction<typeof listCareActivities>;
  const prescriptions = listPrescriptions as jest.MockedFunction<typeof listPrescriptions>;
  const byCode = getWorkflowDefinitionByCode as jest.MockedFunction<typeof getWorkflowDefinitionByCode>;

  beforeEach(() => {
    activities.mockReset();
    prescriptions.mockReset();
    byCode.mockReset();
  });

  it("reuses an existing care activity workflow id", async () => {
    activities.mockResolvedValue([
      { workflow_definition_id: "wf-existing" } as never,
    ]);
    prescriptions.mockResolvedValue([]);
    await expect(resolveCareWorkflowDefinitionId("elder-1")).resolves.toBe("wf-existing");
    expect(byCode).not.toHaveBeenCalled();
  });

  it("returns null when the temporary catalog lookup is missing", async () => {
    activities.mockResolvedValue([]);
    prescriptions.mockResolvedValue([]);
    byCode.mockRejectedValue(new ApiError(404, { detail: "Not found." }, "Not found."));
    await expect(resolveCareWorkflowDefinitionId("elder-1")).resolves.toBeNull();
  });
});

describe("navigation", () => {
  it("routes alert deep links to the stack screen, not a tab", () => {
    expect(routeFromPushPayload({ type: "alert" })).toBe("/(app)/alerts");
    expect(routeFromPushPayload({ alert_id: "abc" })).toBe("/(app)/alerts/abc");
  });

  it("puts Call in the tab bar instead of Alerts", () => {
    expect(APP_TABS.map((tab) => tab.match)).toEqual(["home", "program", "call", "devices", "more"]);
    expect(APP_TABS.some((tab) => tab.match === "alerts")).toBe(false);
  });
});

describe("entitlement labels", () => {
  it("uses Persian labels instead of plan names", () => {
    expect(entitlementLabel("PILLBOX_SUPPORT")).toBe("جعبه دارو");
    expect(entitlementLabel("MAX_CAREGIVERS")).toBe("سقف مراقبان");
  });
});
