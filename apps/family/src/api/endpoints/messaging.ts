import { apiRequest } from "../client";
import { API_BASE_URL } from "../config";
import type { Message, MessageAttachment, SendMessageRequest } from "../types";

export type ListMessagesOptions = {
  since?: number | string;
  limit?: number;
};

export function listMessages(
  elderId: string,
  options: ListMessagesOptions = {},
): Promise<Message[]> {
  const query: Record<string, string | number | undefined> = {};
  if (options.since !== undefined) {
    query.since = options.since;
  }
  if (options.limit !== undefined) {
    query.limit = options.limit;
  }
  return apiRequest<Message[]>(`/elders/${elderId}/messages/`, { query });
}

export function sendMessage(
  elderId: string,
  body: SendMessageRequest,
): Promise<Message> {
  return apiRequest<Message>(`/elders/${elderId}/messages/`, {
    method: "POST",
    body,
  });
}

export function markMessageDelivered(messageId: string): Promise<Message> {
  return apiRequest<Message>(`/messages/${messageId}/delivered/`, {
    method: "POST",
  });
}

export function markMessageRead(messageId: string): Promise<Message> {
  return apiRequest<Message>(`/messages/${messageId}/read/`, {
    method: "POST",
  });
}

export function uploadMedia(formData: FormData): Promise<MessageAttachment> {
  return apiRequest<MessageAttachment>("/media/upload/", {
    method: "POST",
    body: formData,
  });
}

export function getMediaDownloadUrl(attachmentId: string, token?: string | null): string {
  const base = API_BASE_URL.replace(/\/$/, "");
  if (token) {
    return `${base}/media/${attachmentId}/download/?token=${encodeURIComponent(token)}`;
  }
  return `${base}/media/${attachmentId}/download/`;
}
