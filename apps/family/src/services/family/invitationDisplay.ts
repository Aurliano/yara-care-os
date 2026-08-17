import type { RoleCode } from "../../api/types";
import { t } from "../../i18n";

export function roleLabel(code: RoleCode | string): string {
  if (code === "PRIMARY_CAREGIVER") return t.rolePrimary;
  if (code === "CAREGIVER") return t.roleCaregiver;
  if (code === "VIEWER") return t.roleViewer;
  return t.roleCaregiver;
}

export function pendingInvitationTitle(): string {
  return t.pendingInvitationTitle;
}

export function invitationShareMessage(role: string, inviteCode: string): string {
  return `${t.inviteShareHeadline}\n${t.roleCode}: ${role}\n${t.inviteCode}: ${inviteCode}`;
}

export function usesInviteCodeAsName(displayedName: string, inviteCode: string): boolean {
  return displayedName.trim() === inviteCode.trim();
}
