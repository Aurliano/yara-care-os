import { useCallback, useEffect, useRef, useState } from "react";
import { AppState, Linking } from "react-native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { checkout } from "../api/endpoints/payment";
import { getActiveLicense, getEntitlements, listPlans } from "../api/endpoints/licensing";
import { queryKeys } from "../api/queryKeys";
import type { BillingInterval, CheckoutResponse } from "../api/types";
import { mapCheckoutError, mapLicenseToPresentation } from "../services/licensing/subscriptionRepository";
import { usePermissions } from "../permissions/usePermission";

export type PaymentFlowState =
  | "IDLE"
  | "CHECKOUT_PENDING"
  | "REVIEW_DIALOG"
  | "GATEWAY_OPEN"
  | "VERIFYING"
  | "PAYMENT_PENDING"
  | "CHECKOUT_ERROR";

export function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function useSubscription(elderId: string | null) {
  const queryClient = useQueryClient();
  const { can } = usePermissions();
  const canManageSubscription = can("MANAGE_SUBSCRIPTION");

  // Server queries
  const licenseQuery = useQuery({
    queryKey: elderId ? queryKeys.license(elderId) : ["license", "none"],
    queryFn: () => (elderId ? getActiveLicense(elderId) : Promise.resolve(null)),
    enabled: Boolean(elderId),
  });

  const plansQuery = useQuery({
    queryKey: queryKeys.plans,
    queryFn: listPlans,
  });

  const entitlementsQuery = useQuery({
    queryKey: elderId ? queryKeys.entitlements(elderId) : ["entitlements", "none"],
    queryFn: () => (elderId ? getEntitlements(elderId) : Promise.resolve({ entitlements: {} })),
    enabled: Boolean(elderId),
  });

  // Client interaction states
  const [selectedPlanCode, setSelectedPlanCode] = useState<string | null>(null);
  const [selectedInterval, setSelectedInterval] = useState<BillingInterval>("MONTHLY");
  const [paymentState, setPaymentState] = useState<PaymentFlowState>("IDLE");
  const [checkoutResponse, setCheckoutResponse] = useState<CheckoutResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Stable idempotency key for the current logical attempt
  const currentIdempotencyKeyRef = useRef<string | null>(null);
  const lastAttemptedSelectionRef = useRef<{ planCode: string; interval: BillingInterval } | null>(null);

  // Set default selected plan once plans load if none selected
  useEffect(() => {
    if (plansQuery.data?.length && !selectedPlanCode) {
      const activeLicense = licenseQuery.data;
      if (activeLicense) {
        setSelectedPlanCode(activeLicense.plan_code);
      } else {
        const firstActive = plansQuery.data.find((p) => p.status === "ACTIVE") ?? plansQuery.data[0];
        if (firstActive) {
          setSelectedPlanCode(firstActive.code);
        }
      }
    }
  }, [plansQuery.data, licenseQuery.data, selectedPlanCode]);

  // Checkout Mutation: calls POST /api/v1/payments/checkout/
  const checkoutMutation = useMutation({
    mutationFn: async (params: { planCode: string; interval: BillingInterval; idempotencyKey: string }) => {
      if (!elderId) {
        throw new Error("No elder selected.");
      }
      return checkout({
        elder_id: elderId,
        plan_code: params.planCode,
        interval: params.interval,
        idempotency_key: params.idempotencyKey,
      });
    },
    onSuccess: (data) => {
      setCheckoutResponse(data);
      setErrorMessage(null);
      setPaymentState("REVIEW_DIALOG");
    },
    onError: (err) => {
      const message = mapCheckoutError(err);
      setErrorMessage(message);
      setPaymentState("CHECKOUT_ERROR");
    },
  });

  // Step A: User taps "Review Order" -> fetches authoritative price
  const handleReviewOrder = useCallback(
    (planCode?: string, interval?: BillingInterval) => {
      if (!canManageSubscription) {
        setErrorMessage("شما اجازه تغییر اشتراک را ندارید.");
        return;
      }
      const targetPlan = planCode || selectedPlanCode;
      const targetInterval = interval || selectedInterval;
      if (!targetPlan || !elderId) {
        return;
      }

      // Check if this is a new deliberate selection or retry
      const isSameSelection =
        lastAttemptedSelectionRef.current?.planCode === targetPlan &&
        lastAttemptedSelectionRef.current?.interval === targetInterval;

      if (!isSameSelection || !currentIdempotencyKeyRef.current) {
        // Deliberate new attempt -> generate fresh key
        currentIdempotencyKeyRef.current = generateIdempotencyKey();
        lastAttemptedSelectionRef.current = { planCode: targetPlan, interval: targetInterval };
      }

      setPaymentState("CHECKOUT_PENDING");
      setErrorMessage(null);
      checkoutMutation.mutate({
        planCode: targetPlan,
        interval: targetInterval,
        idempotencyKey: currentIdempotencyKeyRef.current,
      });
    },
    [canManageSubscription, selectedPlanCode, selectedInterval, elderId, checkoutMutation],
  );

  // Step B: User explicitly confirms "Proceed to Secure Payment" -> opens gateway
  const handleProceedToPayment = useCallback(async () => {
    if (!checkoutResponse?.redirect_url) {
      return;
    }
    setPaymentState("GATEWAY_OPEN");
    try {
      await Linking.openURL(checkoutResponse.redirect_url);
    } catch {
      setErrorMessage("امکان باز کردن صفحه پرداخت فراهم نشد.");
      setPaymentState("CHECKOUT_ERROR");
    }
  }, [checkoutResponse]);

  // Cancel from Review Dialog
  const handleCancelReview = useCallback(() => {
    setPaymentState("IDLE");
    setCheckoutResponse(null);
    setErrorMessage(null);
    currentIdempotencyKeyRef.current = null;
    lastAttemptedSelectionRef.current = null;
  }, []);

  // Authoritative post-gateway refetch
  const refetchAuthoritativeState = useCallback(async () => {
    if (!elderId) return;
    setPaymentState("VERIFYING");
    try {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.license(elderId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.entitlements(elderId) }),
      ]);
      const updatedLicense = await licenseQuery.refetch();
      if (updatedLicense.data?.status === "ACTIVE") {
        setPaymentState("IDLE");
        setCheckoutResponse(null);
        currentIdempotencyKeyRef.current = null;
        lastAttemptedSelectionRef.current = null;
      } else {
        setPaymentState("PAYMENT_PENDING");
      }
    } catch {
      setPaymentState("PAYMENT_PENDING");
    }
  }, [elderId, queryClient, licenseQuery]);

  // App resume recovery listener
  useEffect(() => {
    if (typeof AppState !== "undefined" && typeof AppState.addEventListener === "function") {
      const subscription = AppState.addEventListener("change", (nextState) => {
        if (nextState === "active" && paymentState === "GATEWAY_OPEN") {
          void refetchAuthoritativeState();
        }
      });
      return () => {
        subscription.remove();
      };
    }
  }, [paymentState, refetchAuthoritativeState]);

  const presentation = mapLicenseToPresentation(
    licenseQuery.data ?? null,
    plansQuery.data ?? [],
  );

  return {
    // Data
    license: licenseQuery.data ?? null,
    plans: plansQuery.data ?? [],
    entitlements: entitlementsQuery.data?.entitlements ?? {},
    presentation,

    // Loading & Query states
    isLoading: licenseQuery.isPending || plansQuery.isPending,
    isRefetching: licenseQuery.isRefetching || entitlementsQuery.isRefetching,
    isError: licenseQuery.isError || plansQuery.isError,

    // User selection state
    selectedPlanCode,
    setSelectedPlanCode,
    selectedInterval,
    setSelectedInterval,

    // Two-step checkout state machine
    paymentState,
    checkoutResponse,
    errorMessage,
    isCheckoutLoading: checkoutMutation.isPending,

    // Actions
    canManageSubscription,
    handleReviewOrder,
    handleProceedToPayment,
    handleCancelReview,
    refetchAuthoritativeState,
  };
}
