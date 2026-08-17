import { apiRequest } from "../client";
import type { CommunicationSession, Contact } from "../types";

export function listContacts(elderId: string): Promise<Contact[]> {
  return apiRequest(`/elders/${elderId}/contacts/`);
}

export function createContact(
  elderId: string,
  body: {
    display_name: string;
    phone?: string;
    preferred_channel: "VOICE" | "VIDEO" | "MESSAGE";
  },
): Promise<Contact> {
  return apiRequest(`/elders/${elderId}/contacts/`, { method: "POST", body });
}

export function archiveContact(contactId: string): Promise<Contact> {
  return apiRequest(`/contacts/${contactId}/archive/`, { method: "POST" });
}

export type CallStartResult = {
  sessionId: string;
  joinToken: string;
  expiresAt: string;
};

export function startCall(body: {
  elder_id: string;
  channel: "VOICE" | "VIDEO" | "MESSAGE";
  recipient_contact_id: string;
}): Promise<CallStartResult> {
  return apiRequest("/communication/call/start/", { method: "POST", body });
}

export function endCall(sessionId: string): Promise<{ status: string }> {
  return apiRequest("/communication/call/end/", { method: "POST", body: { session_id: sessionId } });
}

export function listSessions(elderId: string): Promise<CommunicationSession[]> {
  return apiRequest(`/elders/${elderId}/sessions/`);
}

export function acceptSession(sessionId: string): Promise<CommunicationSession> {
  return apiRequest(`/sessions/${sessionId}/accept/`, { method: "POST" });
}
