import { apiRequest } from "../client";
import type { Contact } from "../types";

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
