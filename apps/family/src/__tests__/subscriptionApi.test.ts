import { checkout } from "../api/endpoints/payment";
import { getActiveLicense } from "../api/endpoints/licensing";
import { apiRequest } from "../api/client";
import { ApiError } from "../api/errors";
import * as fs from "fs";
import * as path from "path";

jest.mock("../api/client", () => ({
  apiRequest: jest.fn(),
}));

const apiRequestMock = apiRequest as jest.MockedFunction<typeof apiRequest>;

describe("Subscription & Payment API layer", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("checkout()", () => {
    it("calls POST /payments/checkout/ with correct request fields", async () => {
      apiRequestMock.mockResolvedValueOnce({
        provider_reference: "ref-123",
        redirect_url: "https://gateway.zarinpal.test/pg/StartPay/ref-123",
        invoice_id: "inv-123",
        payment_attempt_id: "att-123",
        amount: "300000",
        currency: "TOMAN",
      });

      const response = await checkout({
        elder_id: "elder-1",
        plan_code: "PLUS",
        interval: "MONTHLY",
        idempotency_key: "idem-key-1",
      });

      expect(apiRequestMock).toHaveBeenCalledWith("/payments/checkout/", {
        method: "POST",
        body: {
          elder_id: "elder-1",
          plan_code: "PLUS",
          interval: "MONTHLY",
          idempotency_key: "idem-key-1",
        },
      });

      expect(response.amount).toBe("300000");
      expect(response.currency).toBe("TOMAN");
      expect(response.redirect_url).toBe("https://gateway.zarinpal.test/pg/StartPay/ref-123");
    });

    it("STRICTLY enforces that client does NOT send amount, currency, or callback_url", async () => {
      apiRequestMock.mockResolvedValueOnce({
        provider_reference: "ref-123",
        redirect_url: "https://gateway.test",
        invoice_id: "inv-1",
        payment_attempt_id: "att-1",
        amount: "150000",
        currency: "TOMAN",
      });

      const requestPayload = {
        elder_id: "elder-1",
        plan_code: "BASIC",
        interval: "MONTHLY" as const,
        idempotency_key: "key-123",
      };

      await checkout(requestPayload);

      const calledBody = apiRequestMock.mock.calls[0][1]?.body as Record<string, unknown>;
      expect(calledBody).not.toHaveProperty("amount");
      expect(calledBody).not.toHaveProperty("currency");
      expect(calledBody).not.toHaveProperty("callback_url");
      expect(calledBody).not.toHaveProperty("merchant_id");
      expect(calledBody).not.toHaveProperty("authority");
    });
  });

  describe("getActiveLicense()", () => {
    it("returns active license on HTTP 200", async () => {
      const mockLicense = {
        id: "lic-1",
        elder_id: "elder-1",
        plan_code: "PLUS",
        status: "ACTIVE" as const,
        valid_from: "2026-09-01T00:00:00Z",
        valid_until: "2026-10-01T00:00:00Z",
        created_at: "2026-09-01T00:00:00Z",
      };
      apiRequestMock.mockResolvedValueOnce(mockLicense);

      const result = await getActiveLicense("elder-1");
      expect(apiRequestMock).toHaveBeenCalledWith("/elders/elder-1/license/");
      expect(result).toEqual(mockLicense);
    });

    it("returns null when server responds with 404 (no active license)", async () => {
      apiRequestMock.mockRejectedValueOnce(
        new ApiError(404, { detail: "License not found" }, "Not Found"),
      );

      const result = await getActiveLicense("elder-1");
      expect(result).toBeNull();
    });

    it("rethrows non-404 API errors (e.g. 500, network failure)", async () => {
      apiRequestMock.mockRejectedValueOnce(
        new ApiError(500, { detail: "Server error" }, "Internal Server Error"),
      );

      await expect(getActiveLicense("elder-1")).rejects.toThrow("Internal Server Error");
    });
  });

  describe("Architectural Guard: verifyPayment must NOT exist in Family App", () => {
    it("proves payment.ts does NOT implement verifyPayment or call /payments/verify/", () => {
      const paymentFilePath = path.resolve(__dirname, "../api/endpoints/payment.ts");
      const content = fs.readFileSync(paymentFilePath, "utf-8");

      expect(content).not.toContain("verifyPayment");
      expect(content).not.toContain("/payments/verify");
      expect(content).not.toContain("callback_url");
      expect(content).not.toContain("ZarinPal");
      expect(content).not.toContain("Stripe");
    });
  });
});
