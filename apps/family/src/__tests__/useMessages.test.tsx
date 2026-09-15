import React from "react";
import { renderHook, waitFor, act } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMessages } from "../hooks/useMessages";
import * as messagingApi from "../api/endpoints/messaging";
import type { Message } from "../api/types";

jest.mock("../api/endpoints/messaging", () => ({
  listMessages: jest.fn(),
  sendMessage: jest.fn(),
  markMessageDelivered: jest.fn(),
  markMessageRead: jest.fn(),
  uploadMedia: jest.fn(),
  getMediaDownloadUrl: jest.fn(),
}));

describe("useMessages Hook", () => {
  let queryClient: QueryClient;

  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    Wrapper.displayName = "QueryClientTestWrapper";
    return Wrapper;
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches messages and automatically marks incoming SENT messages as DELIVERED and READ", async () => {
    const mockMessages: Message[] = [
      {
        id: "msg-incoming-1",
        elder_id: "elder-1",
        direction: "HUB_TO_FAMILY",
        message_type: "TEXT",
        body: "پیام از هاب",
        status: "SENT",
        idempotency_key: "k1",
        created_at: "2026-09-05T10:00:00Z",
        sent_at: "2026-09-05T10:00:01Z",
        delivered_at: null,
        read_at: null,
        sender: { id: "c-1", display_name: "مادر", is_hub: true },
        attachment: null,
      },
    ];

    (messagingApi.listMessages as jest.Mock).mockResolvedValue(mockMessages);
    (messagingApi.markMessageDelivered as jest.Mock).mockResolvedValue({
      ...mockMessages[0],
      status: "DELIVERED",
    });
    (messagingApi.markMessageRead as jest.Mock).mockResolvedValue({
      ...mockMessages[0],
      status: "READ",
    });

    const { result } = renderHook(() => useMessages("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });

    expect(messagingApi.listMessages).toHaveBeenCalledWith("elder-1");
    expect(messagingApi.markMessageDelivered).toHaveBeenCalledWith("msg-incoming-1");
    expect(messagingApi.markMessageRead).toHaveBeenCalledWith("msg-incoming-1");
  });

  it("sorts messages in ascending chronological order (created_at ASC) regardless of server order", async () => {
    // Server returns descending order (-created_at)
    const serverDescending: Message[] = [
      {
        id: "msg-2",
        elder_id: "elder-1",
        direction: "FAMILY_TO_HUB",
        message_type: "TEXT",
        body: "پیام دوم (جدیدتر)",
        status: "DELIVERED",
        idempotency_key: "k2",
        created_at: "2026-09-05T12:00:00Z",
        sent_at: "2026-09-05T12:00:01Z",
        delivered_at: null,
        read_at: null,
        sender: { id: "u-1", display_name: "You", is_hub: false },
        attachment: null,
      },
      {
        id: "msg-1",
        elder_id: "elder-1",
        direction: "HUB_TO_FAMILY",
        message_type: "TEXT",
        body: "پیام اول (قدیمی‌تر)",
        status: "READ",
        idempotency_key: "k1",
        created_at: "2026-09-05T10:00:00Z",
        sent_at: "2026-09-05T10:00:01Z",
        delivered_at: "2026-09-05T10:00:02Z",
        read_at: "2026-09-05T10:00:05Z",
        sender: { id: "c-1", display_name: "مادر", is_hub: true },
        attachment: null,
      },
    ];

    (messagingApi.listMessages as jest.Mock).mockResolvedValue(serverDescending);

    const { result } = renderHook(() => useMessages("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    // Oldest first (10:00), newest last (12:00)
    expect(result.current.messages[0].id).toBe("msg-1");
    expect(result.current.messages[1].id).toBe("msg-2");
  });

  it("sends text message with optimistic update", async () => {
    (messagingApi.listMessages as jest.Mock).mockResolvedValue([]);
    const savedMessage: Message = {
      id: "server-msg-1",
      elder_id: "elder-1",
      direction: "FAMILY_TO_HUB",
      message_type: "TEXT",
      body: "سلام مامان",
      status: "SENT",
      idempotency_key: "idem-1",
      created_at: "2026-09-05T10:00:00Z",
      sent_at: "2026-09-05T10:00:01Z",
      delivered_at: null,
      read_at: null,
      sender: { id: "u-1", display_name: "You", is_hub: false },
      attachment: null,
    };
    (messagingApi.sendMessage as jest.Mock).mockResolvedValue(savedMessage);

    const { result } = renderHook(() => useMessages("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendTextMessage("سلام مامان");
    });

    expect(messagingApi.sendMessage).toHaveBeenCalledTimes(1);
    expect(messagingApi.sendMessage).toHaveBeenCalledWith(
      "elder-1",
      expect.objectContaining({
        direction: "FAMILY_TO_HUB",
        message_type: "TEXT",
        body: "سلام مامان",
      }),
    );

    await waitFor(() => {
      expect(result.current.messages).toEqual(
        expect.arrayContaining([expect.objectContaining({ body: "سلام مامان" })]),
      );
    });
  });

  it("retries sending a failed message with retryMessage", async () => {
    (messagingApi.listMessages as jest.Mock).mockResolvedValue([
      {
        id: "failed-msg-1",
        elder_id: "elder-1",
        direction: "FAMILY_TO_HUB",
        message_type: "TEXT",
        body: "پیام ناموفق قبلی",
        status: "FAILED",
        idempotency_key: "idem-fail",
        created_at: "2026-09-05T10:00:00Z",
        sent_at: null,
        delivered_at: null,
        read_at: null,
        sender: { id: "u-1", display_name: "You", is_hub: false },
        attachment: null,
      },
    ]);

    const sentMessage: Message = {
      id: "retry-success-1",
      elder_id: "elder-1",
      direction: "FAMILY_TO_HUB",
      message_type: "TEXT",
      body: "پیام ناموفق قبلی",
      status: "SENT",
      idempotency_key: "idem-retry",
      created_at: "2026-09-05T10:05:00Z",
      sent_at: "2026-09-05T10:05:01Z",
      delivered_at: null,
      read_at: null,
      sender: { id: "u-1", display_name: "You", is_hub: false },
      attachment: null,
    };
    (messagingApi.sendMessage as jest.Mock).mockResolvedValue(sentMessage);

    const { result } = renderHook(() => useMessages("elder-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });

    await act(async () => {
      await result.current.retryMessage("failed-msg-1");
    });

    expect(messagingApi.sendMessage).toHaveBeenCalledWith(
      "elder-1",
      expect.objectContaining({
        direction: "FAMILY_TO_HUB",
        message_type: "TEXT",
        body: "پیام ناموفق قبلی",
      }),
    );
  });

  it("marks message as read manually", async () => {
    (messagingApi.listMessages as jest.Mock).mockResolvedValue([]);
    (messagingApi.markMessageRead as jest.Mock).mockResolvedValue({
      id: "msg-to-read",
      status: "READ",
    });

    const { result } = renderHook(() => useMessages("elder-1"), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.markAsRead("msg-to-read");
    });

    expect(messagingApi.markMessageRead).toHaveBeenCalledWith("msg-to-read");
  });
});
