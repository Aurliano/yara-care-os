import { apiRequest } from "../client";
import type {
  Elder,
  EmergencyRecipient,
  Invitation,
  Membership,
  PermissionCode,
  User,
} from "../types";

export function registerUser(body: {
  phone: string;
  password: string;
  full_name: string;
  email?: string;
}): Promise<User> {
  return apiRequest("/auth/register/", { method: "POST", auth: false, body });
}

export function getCurrentUser(): Promise<User> {
  return apiRequest("/users/me/");
}

export function updateCurrentUser(body: { full_name?: string; email?: string }): Promise<User> {
  return apiRequest("/users/me/", { method: "PATCH", body });
}

export function listElders(): Promise<Elder[]> {
  return apiRequest("/elders/");
}

export function getElder(elderId: string): Promise<Elder> {
  return apiRequest(`/elders/${elderId}/`);
}

export function createElder(body: { full_name: string; birth_date?: string | null }): Promise<Elder> {
  return apiRequest("/elders/", { method: "POST", body });
}

export function listMembers(elderId: string): Promise<Membership[]> {
  return apiRequest(`/elders/${elderId}/members/`);
}

export function changeMemberRole(
  elderId: string,
  membershipId: string,
  role_code: string,
): Promise<Membership> {
  return apiRequest(`/elders/${elderId}/members/${membershipId}/role/`, {
    method: "PATCH",
    body: { role_code },
  });
}

export function suspendMember(elderId: string, membershipId: string): Promise<Membership> {
  return apiRequest(`/elders/${elderId}/members/${membershipId}/suspend/`, { method: "POST" });
}

export function revokeMember(elderId: string, membershipId: string): Promise<Membership> {
  return apiRequest(`/elders/${elderId}/members/${membershipId}/revoke/`, { method: "POST" });
}

export function listInvitations(elderId: string): Promise<Invitation[]> {
  return apiRequest(`/elders/${elderId}/invitations/`);
}

export function createInvitation(
  elderId: string,
  body: { role_code: string; expires_at: string },
): Promise<Invitation> {
  return apiRequest(`/elders/${elderId}/invitations/`, { method: "POST", body });
}

export function revokeInvitation(elderId: string, invitationId: string): Promise<Invitation> {
  return apiRequest(`/elders/${elderId}/invitations/${invitationId}/revoke/`, { method: "POST" });
}

export function acceptInvitation(invite_code: string): Promise<Membership> {
  return apiRequest("/invitations/accept/", { method: "POST", body: { invite_code } });
}

export function getMyPermissions(elderId: string): Promise<{ permissions: PermissionCode[] }> {
  return apiRequest(`/elders/${elderId}/permissions/me/`);
}

export function checkPermission(
  elderId: string,
  permission_code: PermissionCode,
): Promise<{ allowed: boolean }> {
  return apiRequest(`/elders/${elderId}/permissions/check/`, {
    method: "POST",
    body: { permission_code },
  });
}

export function listEmergencyRecipients(elderId: string): Promise<EmergencyRecipient[]> {
  return apiRequest(`/elders/${elderId}/emergency-recipients/`);
}

export function configureEmergencyRecipients(
  elderId: string,
  membership_ids: string[],
): Promise<EmergencyRecipient[]> {
  return apiRequest(`/elders/${elderId}/emergency-recipients/`, {
    method: "PUT",
    body: { membership_ids },
  });
}
