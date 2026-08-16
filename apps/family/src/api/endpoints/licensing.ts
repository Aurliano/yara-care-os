import { apiRequest } from "../client";
import type { EntitlementKey, EntitlementMap, License, Plan } from "../types";

export function listPlans(): Promise<Plan[]> {
  return apiRequest("/plans/");
}

export function getEntitlements(elderId: string): Promise<{ entitlements: EntitlementMap }> {
  return apiRequest(`/elders/${elderId}/entitlements/`);
}

export function checkEntitlement(
  elderId: string,
  entitlement_key: EntitlementKey,
): Promise<{ allowed: boolean }> {
  return apiRequest(`/elders/${elderId}/entitlements/check/`, {
    method: "POST",
    body: { entitlement_key },
  });
}

export function getEntitlementLimit(
  elderId: string,
  entitlementKey: EntitlementKey,
): Promise<{ limit: number | null }> {
  return apiRequest(`/elders/${elderId}/entitlements/limits/${entitlementKey}/`);
}

export function changePlan(elderId: string, licenseId: string, plan_code: string): Promise<License> {
  return apiRequest(`/elders/${elderId}/license/${licenseId}/change-plan/`, {
    method: "POST",
    body: { plan_code },
  });
}
