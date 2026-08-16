import type { PermissionCode } from "../api/types";

export const PERMISSIONS = {
  VIEW_ELDER_STATUS: "VIEW_ELDER_STATUS",
  MANAGE_MEDICATION: "MANAGE_MEDICATION",
  MANAGE_CONTACTS: "MANAGE_CONTACTS",
  MANAGE_DEVICES: "MANAGE_DEVICES",
  INITIATE_CALL: "INITIATE_CALL",
  MANAGE_MEMBERS: "MANAGE_MEMBERS",
  MANAGE_SUBSCRIPTION: "MANAGE_SUBSCRIPTION",
} as const satisfies Record<PermissionCode, PermissionCode>;

export function hasPermission(
  granted: readonly PermissionCode[] | undefined,
  code: PermissionCode,
): boolean {
  return Boolean(granted?.includes(code));
}
