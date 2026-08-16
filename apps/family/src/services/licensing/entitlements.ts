import type { EntitlementKey, EntitlementMap } from "../../api/types";

export function hasEntitlement(map: EntitlementMap, key: EntitlementKey): boolean {
  const value = map[key];
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value > 0;
  }
  return false;
}
