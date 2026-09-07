import {
  getMediaDownloadUrl,
  listMessages,
  markMessageDelivered,
  markMessageRead,
  sendMessage,
  uploadMedia,
} from "../api/endpoints/messaging";
import { API_BASE_URL } from "../api/config";
import { ApiError, mapMessagingError } from "../api/errors";
import { t } from "../i18n";
import type { Message, MessageAttachment, SendMessageRequest } from "../api/types";

describe("Messaging Endpoints", () => {
  const originalFetch = global.fetch;
  let fetchMock: jest.Mock;

  beforeEach(() => {
    fetchMock = jest.fn();
    global.fetch = fetchMock;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("listMessages calls GET /elders/{elderId}/messages/ with query params", async () => {
    const mockMessages: Message[] = [
      {
        id: "msg-1",
        elder_id: "elder-1",
        direction: "HUB_TO_FAMILY",
        message_type: "TEXT",
        body: "سلام دخترم",
        status: "SENT",
        idempotency_key: "k1",
        created_at: "2026-09-05T10:00:00Z",
        sent_at: "2026-09-05T10:00:01Z",
        delivered_at: null,
        read_at: null,
        sender: { id: "contact-1", display_name: "مادر", is_hub: true },
        attachment: null,
      },
    ];

    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockMessages),
    });

    const result = await listMessages("elder-1", { since: "2026-09-05T00:00:00Z", limit: 20 });

    expect(result).toEqual(mockMessages);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledOptions] = fetchMock.mock.calls[0];
    expect(calledUrl).toContain("/elders/elder-1/messages/");
    expect(calledUrl).toContain("limit=20");
    expect(calledOptions.method).toBe("GET");
  });

  it("sendMessage calls POST /elders/{elderId}/messages/ with payload", async () => {
    const payload: SendMessageRequest = {
      direction: "FAMILY_TO_HUB",
      message_type: "TEXT",
      body: "سلام مامان جان",
      idempotency_key: "idem-123",
    };

    const mockResponse: Message = {
      id: "msg-2",
      elder_id: "elder-1",
      direction: "FAMILY_TO_HUB",
      message_type: "TEXT",
      body: "سلام مامان جان",
      status: "SENT",
      idempotency_key: "idem-123",
      created_at: "2026-09-05T10:05:00Z",
      sent_at: "2026-09-05T10:05:01Z",
      delivered_at: null,
      read_at: null,
      sender: { id: "user-1", display_name: "Caregiver", is_hub: false },
      attachment: null,
    };

    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 201,
      text: async () => JSON.stringify(mockResponse),
    });

    const result = await sendMessage("elder-1", payload);

    expect(result).toEqual(mockResponse);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledOptions] = fetchMock.mock.calls[0];
    expect(calledUrl).toContain("/elders/elder-1/messages/");
    expect(calledOptions.method).toBe("POST");
    expect(JSON.parse(calledOptions.body)).toEqual(payload);
  });

  it("markMessageDelivered calls POST /messages/{id}/delivered/", async () => {
    const mockDelivered: Partial<Message> = {
      id: "msg-1",
      status: "DELIVERED",
      delivered_at: "2026-09-05T10:06:00Z",
    };

    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockDelivered),
    });

    const result = await markMessageDelivered("msg-1");

    expect(result.status).toBe("DELIVERED");
    const [calledUrl, calledOptions] = fetchMock.mock.calls[0];
    expect(calledUrl).toContain("/messages/msg-1/delivered/");
    expect(calledOptions.method).toBe("POST");
  });

  it("markMessageRead calls POST /messages/{id}/read/", async () => {
    const mockRead: Partial<Message> = {
      id: "msg-1",
      status: "READ",
      read_at: "2026-09-05T10:07:00Z",
    };

    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockRead),
    });

    const result = await markMessageRead("msg-1");

    expect(result.status).toBe("READ");
    const [calledUrl, calledOptions] = fetchMock.mock.calls[0];
    expect(calledUrl).toContain("/messages/msg-1/read/");
    expect(calledOptions.method).toBe("POST");
  });

  it("uploadMedia sends FormData without json Content-Type header", async () => {
    const mockAttachment: MessageAttachment = {
      id: "att-1",
      file_size: 1024,
      mime_type: "audio/m4a",
      duration_seconds: 12.5,
      width: null,
      height: null,
      original_filename: "voice.m4a",
      created_at: "2026-09-05T10:08:00Z",
      download_url: "/api/v1/media/att-1/download/",
    };

    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 201,
      text: async () => JSON.stringify(mockAttachment),
    });

    const formData = new FormData();
    formData.append("media_type", "VOICE");

    const result = await uploadMedia(formData);

    expect(result).toEqual(mockAttachment);
    const [calledUrl, calledOptions] = fetchMock.mock.calls[0];
    expect(calledUrl).toContain("/media/upload/");
    expect(calledOptions.method).toBe("POST");
    expect(calledOptions.body).toBe(formData);
    // Crucial: Content-Type must not be forced to application/json for FormData
    expect(calledOptions.headers["Content-Type"]).toBeUndefined();
  });

  it("getMediaDownloadUrl constructs full absolute URL", () => {
    const url = getMediaDownloadUrl("att-99");
    const base = API_BASE_URL.replace(/\/$/, "");
    expect(url).toBe(`${base}/media/att-99/download/`);
  });

  describe("mapMessagingError", () => {
    it("maps 403 ApiError to messagePermissionDenied", () => {
      const err = new ApiError(403, { detail: "User does not have permission to send messages." }, "Forbidden");
      expect(mapMessagingError(err)).toBe(t.messagePermissionDenied);
    });

    it("surfaces server detail string for non-403 ApiError", () => {
      const err = new ApiError(400, { detail: "Message body cannot be empty." }, "Bad Request");
      expect(mapMessagingError(err)).toBe("Message body cannot be empty.");
    });

    it("falls back to messageSendFailed for generic errors", () => {
      expect(mapMessagingError(new Error("Network failed"))).toBe(t.messageSendFailed);
      expect(mapMessagingError(null)).toBe(t.messageSendFailed);
    });
  });
});
