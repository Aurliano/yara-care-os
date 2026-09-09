import { apiRequest } from "../client";
import type { CheckoutRequest, CheckoutResponse } from "../types";

/**
 * Request server-authoritative checkout for an Elder subscription.
 * Note: Amount and currency are resolved server-side by the backend.
 * The client request contains only elder_id, plan_code, interval, and optional idempotency/contact metadata.
 */
export function checkout(request: CheckoutRequest): Promise<CheckoutResponse> {
  return apiRequest<CheckoutResponse>("/payments/checkout/", {
    method: "POST",
    body: request,
  });
}
