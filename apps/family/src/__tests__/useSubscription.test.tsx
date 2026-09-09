import React from "react";
import { act, renderHook, waitFor } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Linking } from "react-native";
import { useSubscription } from "../hooks/useSubscription";
import * as paymentApi from "../api/endpoints/payment";
import * as licensingApi from "../api/endpoints/licensing";
import * as permissionHook from "../permissions/usePermission";

jest.mock("../api/endpoints/payment");
jest.mock("../api/endpoints/licensing");
jest.mock("../permissions/usePermission");

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  Wrapper.displayName = "TestQueryWrapper";
  return Wrapper;
}

describe("useSubscription hook", () => {
  const mockLicense = {
    id: "lic-1",
    elder_id: "elder-1",
    plan_code: "PLUS",
    status: "ACTIVE" as const,
    valid_from: "2026-09-01T00:00:00Z",
    valid_until: "2026-10-01T00:00:00Z",
    created_at: "2026-09-01T00:00:00Z",
  };

  const mockPlans = [
    { id: "p-1", code: "BASIC", name: "طرح پایه", status: "ACTIVE" as const, created_at: "2026-01-01T00:00:00Z" },
    { id: "p-2", code: "PLUS", name: "طرح پلاس", status: "ACTIVE" as const, created_at: "2026-01-01T00:00:00Z" },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (licensingApi.getActiveLicense as jest.Mock).mockResolvedValue(mockLicense);
    (licensingApi.listPlans as jest.Mock).mockResolvedValue(mockPlans);
    (licensingApi.getEntitlements as jest.Mock).mockResolvedValue({ entitlements: {} });
    (permissionHook.usePermissions as jest.Mock).mockReturnValue({
      can: (code: string) => code === "MANAGE_SUBSCRIPTION",
      granted: ["MANAGE_SUBSCRIPTION"],
    });
  });

  it("initializes in IDLE state with server data loaded", async () => {
    const { result } = renderHook(() => useSubscription("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.paymentState).toBe("IDLE");
    expect(result.current.license?.plan_code).toBe("PLUS");
    expect(result.current.plans.length).toBe(2);
    expect(result.current.canManageSubscription).toBe(true);
  });

  it("Step A: handleReviewOrder requests server-authoritative checkout and enters REVIEW_DIALOG", async () => {
    (paymentApi.checkout as jest.Mock).mockResolvedValueOnce({
      provider_reference: "ref-999",
      redirect_url: "https://gateway.bank.test/pay/ref-999",
      invoice_id: "inv-999",
      payment_attempt_id: "att-999",
      amount: "300000",
      currency: "TOMAN",
    });

    const { result } = renderHook(() => useSubscription("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.handleReviewOrder("PLUS", "MONTHLY");
    });

    await waitFor(() => {
      expect(result.current.paymentState).toBe("REVIEW_DIALOG");
    });

    expect(paymentApi.checkout).toHaveBeenCalledTimes(1);
    const checkoutCall = (paymentApi.checkout as jest.Mock).mock.calls[0][0];
    expect(checkoutCall.elder_id).toBe("elder-1");
    expect(checkoutCall.plan_code).toBe("PLUS");
    expect(checkoutCall.interval).toBe("MONTHLY");
    expect(checkoutCall.idempotency_key).toBeDefined();

    // Server-resolved price is stored
    expect(result.current.checkoutResponse?.amount).toBe("300000");
    expect(result.current.checkoutResponse?.currency).toBe("TOMAN");
  });

  it("Idempotency: reuses the same key for retry of exact same selection, generates new key for deliberate change", async () => {
    (paymentApi.checkout as jest.Mock)
      .mockRejectedValueOnce(new Error("Network glitch"))
      .mockResolvedValueOnce({
        provider_reference: "ref-1",
        redirect_url: "https://gateway.bank.test/pay/ref-1",
        invoice_id: "inv-1",
        payment_attempt_id: "att-1",
        amount: "300000",
        currency: "TOMAN",
      })
      .mockResolvedValueOnce({
        provider_reference: "ref-2",
        redirect_url: "https://gateway.bank.test/pay/ref-2",
        invoice_id: "inv-2",
        payment_attempt_id: "att-2",
        amount: "2500000",
        currency: "TOMAN",
      });

    const { result } = renderHook(() => useSubscription("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // First attempt -> fails
    act(() => {
      result.current.handleReviewOrder("PLUS", "MONTHLY");
    });
    await waitFor(() => expect(result.current.paymentState).toBe("CHECKOUT_ERROR"));
    const firstKey = (paymentApi.checkout as jest.Mock).mock.calls[0][0].idempotency_key;

    // Retry of same selection -> reuses same key!
    act(() => {
      result.current.handleReviewOrder("PLUS", "MONTHLY");
    });
    await waitFor(() => expect(result.current.paymentState).toBe("REVIEW_DIALOG"));
    const retryKey = (paymentApi.checkout as jest.Mock).mock.calls[1][0].idempotency_key;
    expect(retryKey).toBe(firstKey);

    // Deliberate change of interval to ANNUAL -> generates new key!
    act(() => {
      result.current.handleReviewOrder("PLUS", "ANNUAL");
    });
    await waitFor(() => expect(result.current.paymentState).toBe("REVIEW_DIALOG"));
    const deliberateNewKey = (paymentApi.checkout as jest.Mock).mock.calls[2][0].idempotency_key;
    expect(deliberateNewKey).not.toBe(firstKey);
  });

  it("Step B: handleProceedToPayment opens redirect_url without calling checkout again", async () => {
    (paymentApi.checkout as jest.Mock).mockResolvedValueOnce({
      provider_reference: "ref-1",
      redirect_url: "https://gateway.bank.test/pay/ref-1",
      invoice_id: "inv-1",
      payment_attempt_id: "att-1",
      amount: "300000",
      currency: "TOMAN",
    });

    const { result } = renderHook(() => useSubscription("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.handleReviewOrder("PLUS", "MONTHLY");
    });
    await waitFor(() => expect(result.current.paymentState).toBe("REVIEW_DIALOG"));

    // User explicitly confirms "Proceed to Secure Payment"
    await act(async () => {
      await result.current.handleProceedToPayment();
    });

    expect(Linking.openURL).toHaveBeenCalledWith("https://gateway.bank.test/pay/ref-1");
    // Checkout was called exactly once (during Step A), NOT again during Step B!
    expect(paymentApi.checkout).toHaveBeenCalledTimes(1);
    expect(result.current.paymentState).toBe("GATEWAY_OPEN");
  });

  it("handleCancelReview dismisses review dialog without opening gateway", async () => {
    (paymentApi.checkout as jest.Mock).mockResolvedValueOnce({
      provider_reference: "ref-1",
      redirect_url: "https://gateway.bank.test/pay/ref-1",
      invoice_id: "inv-1",
      payment_attempt_id: "att-1",
      amount: "300000",
      currency: "TOMAN",
    });

    const { result } = renderHook(() => useSubscription("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.handleReviewOrder("PLUS", "MONTHLY");
    });
    await waitFor(() => expect(result.current.paymentState).toBe("REVIEW_DIALOG"));

    act(() => {
      result.current.handleCancelReview();
    });

    expect(result.current.paymentState).toBe("IDLE");
    expect(result.current.checkoutResponse).toBeNull();
    expect(Linking.openURL).not.toHaveBeenCalled();
  });

  it("Permission Guard: blocks checkout when caregiver lacks MANAGE_SUBSCRIPTION", async () => {
    (permissionHook.usePermissions as jest.Mock).mockReturnValue({
      can: () => false,
      granted: [],
    });

    const { result } = renderHook(() => useSubscription("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.handleReviewOrder("PLUS", "MONTHLY");
    });

    expect(paymentApi.checkout).not.toHaveBeenCalled();
    expect(result.current.errorMessage).toContain("اجازه");
  });
});
