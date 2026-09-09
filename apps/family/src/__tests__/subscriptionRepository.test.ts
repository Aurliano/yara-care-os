import {
  formatPrice,
  intervalLabel,
  mapCheckoutError,
  mapLicenseToPresentation,
} from "../services/licensing/subscriptionRepository";
import { ApiError } from "../api/errors";
import type { License, Plan } from "../api/types";

describe("subscriptionRepository presentation layer", () => {
  const mockPlans: Plan[] = [
    { id: "p-1", code: "BASIC", name: "طرح پایه", status: "ACTIVE", created_at: "2026-01-01T00:00:00Z" },
    { id: "p-2", code: "PLUS", name: "طرح پلاس", status: "ACTIVE", created_at: "2026-01-01T00:00:00Z" },
  ];

  describe("mapLicenseToPresentation()", () => {
    it("maps null license to NO_LICENSE state", () => {
      const presentation = mapLicenseToPresentation(null, mockPlans);
      expect(presentation.displayStatus).toBe("NO_LICENSE");
      expect(presentation.statusTone).toBe("neutral");
      expect(presentation.validUntilFormatted).toBeNull();
      expect(presentation.planName).toBeNull();
    });

    it("maps active license with future valid_until to ACTIVE state", () => {
      const futureDate = new Date(Date.now() + 86400000 * 30).toISOString();
      const license: License = {
        id: "lic-1",
        elder_id: "elder-1",
        plan_code: "PLUS",
        status: "ACTIVE",
        valid_from: "2026-09-01T00:00:00Z",
        valid_until: futureDate,
        created_at: "2026-09-01T00:00:00Z",
      };

      const presentation = mapLicenseToPresentation(license, mockPlans);
      expect(presentation.displayStatus).toBe("ACTIVE");
      expect(presentation.statusTone).toBe("success");
      expect(presentation.planName).toBe("طرح پلاس");
      expect(presentation.validUntilFormatted).not.toBeNull();
    });

    it("maps active license with past valid_until to EXPIRED state", () => {
      const pastDate = new Date(Date.now() - 86400000).toISOString();
      const license: License = {
        id: "lic-1",
        elder_id: "elder-1",
        plan_code: "PLUS",
        status: "ACTIVE",
        valid_from: "2026-08-01T00:00:00Z",
        valid_until: pastDate,
        created_at: "2026-08-01T00:00:00Z",
      };

      const presentation = mapLicenseToPresentation(license, mockPlans);
      expect(presentation.displayStatus).toBe("EXPIRED");
      expect(presentation.statusTone).toBe("warning");
    });

    it("maps SUSPENDED license correctly", () => {
      const license: License = {
        id: "lic-2",
        elder_id: "elder-1",
        plan_code: "BASIC",
        status: "SUSPENDED",
        valid_from: "2026-08-01T00:00:00Z",
        valid_until: null,
        created_at: "2026-08-01T00:00:00Z",
      };

      const presentation = mapLicenseToPresentation(license, mockPlans);
      expect(presentation.displayStatus).toBe("SUSPENDED");
      expect(presentation.statusTone).toBe("warning");
    });

    it("maps REVOKED license correctly", () => {
      const license: License = {
        id: "lic-3",
        elder_id: "elder-1",
        plan_code: "BASIC",
        status: "REVOKED",
        valid_from: "2026-08-01T00:00:00Z",
        valid_until: null,
        created_at: "2026-08-01T00:00:00Z",
      };

      const presentation = mapLicenseToPresentation(license, mockPlans);
      expect(presentation.displayStatus).toBe("REVOKED");
      expect(presentation.statusTone).toBe("error");
    });
  });

  describe("formatPrice()", () => {
    it("formats server amount and currency with Persian digits and separator", () => {
      const result = formatPrice("300000", "TOMAN");
      expect(result).toContain("۳۰۰,۰۰۰");
      expect(result).toContain("تومان");
    });

    it("handles number inputs gracefully", () => {
      const result = formatPrice(1500000, "TOMAN");
      expect(result).toContain("۱,۵۰۰,۰۰۰");
      expect(result).toContain("تومان");
    });
  });

  describe("intervalLabel()", () => {
    it("returns correct localized interval text", () => {
      expect(intervalLabel("MONTHLY")).toBe("ماهانه");
      expect(intervalLabel("ANNUAL")).toBe("سالانه");
    });
  });

  describe("mapCheckoutError()", () => {
    it("maps 403 to permission denied message", () => {
      const err = new ApiError(403, { detail: "Forbidden" }, "Forbidden");
      expect(mapCheckoutError(err)).toContain("اجازه");
    });

    it("maps 404 to not found message", () => {
      const err = new ApiError(404, { detail: "Not found" }, "Not Found");
      expect(mapCheckoutError(err)).toContain("یافت نشد");
    });

    it("maps generic errors to calm network error message", () => {
      expect(mapCheckoutError(new Error("Network failed"))).toContain("خطا در برقراری ارتباط");
    });
  });
});
