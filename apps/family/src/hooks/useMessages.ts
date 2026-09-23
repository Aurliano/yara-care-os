import { useCallback, useEffect, useMemo, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listMessages,
  markMessageDelivered,
  markMessageRead,
  sendMessage,
  uploadMedia,
} from "../api/endpoints/messaging";
import { queryKeys } from "../api/queryKeys";
import type { Message, MessageType, SendMessageRequest } from "../api/types";

export type SendMediaParams = {
  file: { uri: string; name: string; type: string } | Blob;
  mediaType: MessageType;
  body?: string;
  durationSeconds?: number;
  width?: number;
  height?: number;
};

function deduplicateAndSort(messages: Message[]): Message[] {
  const byId = new Map<string, Message>();
  const byIdempotency = new Map<string, Message>();

  for (const msg of messages) {
    if (msg.idempotency_key && byIdempotency.has(msg.idempotency_key)) {
      const existing = byIdempotency.get(msg.idempotency_key)!;
      if (existing.id.startsWith("temp_") && !msg.id.startsWith("temp_")) {
        byId.delete(existing.id);
        byId.set(msg.id, msg);
        byIdempotency.set(msg.idempotency_key, msg);
      }
      continue;
    }
    byId.set(msg.id, msg);
    if (msg.idempotency_key) {
      byIdempotency.set(msg.idempotency_key, msg);
    }
  }

  return Array.from(byId.values()).sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );
}

export function useMessages(
  elderId: string | null | undefined,
  options?: { autoMarkRead?: boolean },
) {
  const queryClient = useQueryClient();
  const deliveredAcks = useRef<Set<string>>(new Set());
  const readAcks = useRef<Set<string>>(new Set());

  const messagesQueryKey = useMemo(
    () => (elderId ? queryKeys.messages(elderId) : ["messages"]),
    [elderId],
  );

  const query = useQuery({
    queryKey: messagesQueryKey,
    enabled: Boolean(elderId),
    queryFn: async () => {
      const serverMessages = await listMessages(elderId as string);
      const currentCache = queryClient.getQueryData<Message[]>(messagesQueryKey) ?? [];
      const inFlightOrFailed = currentCache.filter(
        (local) =>
          (local.status === "PENDING" || local.status === "FAILED") &&
          !serverMessages.some(
            (server) =>
              server.id === local.id ||
              (server.idempotency_key &&
                local.idempotency_key &&
                server.idempotency_key === local.idempotency_key),
          ),
      );
      return deduplicateAndSort([...serverMessages, ...inFlightOrFailed]);
    },
    refetchInterval: 3000,
  });

  const rawMessages = query.data;
  const messages = useMemo(() => {
    return deduplicateAndSort(rawMessages ?? []);
  }, [rawMessages]);

  // Automatically acknowledge delivery and read for incoming HUB_TO_FAMILY messages
  useEffect(() => {
    if (!messages.length) return;
    for (const msg of messages) {
      if (msg.direction === "HUB_TO_FAMILY") {
        if (msg.status === "SENT" && !deliveredAcks.current.has(msg.id)) {
          deliveredAcks.current.add(msg.id);
          markMessageDelivered(msg.id)
            .then((updated) => {
              queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
                prev.map((m) =>
                  m.id === msg.id
                    ? { ...m, status: updated.status, delivered_at: updated.delivered_at }
                    : m,
                ),
              );
            })
            .catch(() => {
              deliveredAcks.current.delete(msg.id);
            });
        }
        if (
          options?.autoMarkRead !== false &&
          msg.status !== "READ" &&
          !msg.read &&
          !readAcks.current.has(msg.id)
        ) {
          readAcks.current.add(msg.id);
          markMessageRead(msg.id)
            .then((updated) => {
              queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
                prev.map((m) =>
                  m.id === msg.id
                    ? { ...m, status: "READ", read: true, read_at: updated.read_at }
                    : m,
                ),
              );
            })
            .catch(() => {
              readAcks.current.delete(msg.id);
            });
        }
      }
    }
  }, [messages, messagesQueryKey, options?.autoMarkRead, queryClient]);

  const markAsRead = useCallback(
    async (messageId: string) => {
      try {
        const updated = await markMessageRead(messageId);
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
          prev.map((m) => (m.id === messageId ? updated : m)),
        );
      } catch {
        // Best-effort read acknowledgement
      }
    },
    [messagesQueryKey, queryClient],
  );

  const sendTextMutation = useMutation({
    mutationFn: async (text: string) => {
      if (!elderId) throw new Error("Elder ID is required");
      const idempotencyKey = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      const request: SendMessageRequest = {
        direction: "FAMILY_TO_HUB",
        message_type: "TEXT",
        body: text,
        idempotency_key: idempotencyKey,
      };

      const optimisticId = `temp_${Date.now()}`;
      const optimisticMessage: Message = {
        id: optimisticId,
        elder_id: elderId,
        direction: "FAMILY_TO_HUB",
        message_type: "TEXT",
        body: text,
        status: "PENDING",
        idempotency_key: idempotencyKey,
        created_at: new Date().toISOString(),
        sent_at: null,
        delivered_at: null,
        read_at: null,
        sender: { id: null, display_name: "You", is_hub: false },
        attachment: null,
      };

      queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
        deduplicateAndSort([...prev, optimisticMessage]),
      );

      try {
        const saved = await sendMessage(elderId, request);
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
          deduplicateAndSort(
            prev.map((m) =>
              m.id === optimisticId || m.idempotency_key === idempotencyKey ? saved : m,
            ),
          ),
        );
        return saved;
      } catch (err) {
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
          prev.map((m) =>
            m.id === optimisticId ? { ...m, status: "FAILED" as const } : m,
          ),
        );
        throw err;
      }
    },
  });

  const sendMediaMutation = useMutation({
    mutationFn: async (params: SendMediaParams) => {
      if (!elderId) throw new Error("Elder ID is required");

      const formData = new FormData();
      if ("uri" in params.file) {
        formData.append("file", {
          uri: params.file.uri,
          name: params.file.name,
          type: params.file.type,
        } as unknown as Blob);
      } else {
        formData.append("file", params.file);
      }
      formData.append("media_type", params.mediaType);
      if (params.durationSeconds !== undefined) {
        formData.append("duration_seconds", String(params.durationSeconds));
      }
      if (params.width !== undefined) {
        formData.append("width", String(params.width));
      }
      if (params.height !== undefined) {
        formData.append("height", String(params.height));
      }

      const idempotencyKey = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      const optimisticId = `temp_${Date.now()}`;
      const optimisticMessage: Message = {
        id: optimisticId,
        elder_id: elderId,
        direction: "FAMILY_TO_HUB",
        message_type: params.mediaType,
        body: params.body ?? "",
        status: "PENDING",
        idempotency_key: idempotencyKey,
        created_at: new Date().toISOString(),
        sent_at: null,
        delivered_at: null,
        read_at: null,
        sender: { id: null, display_name: "You", is_hub: false },
        attachment: null,
      };

      queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
        deduplicateAndSort([...prev, optimisticMessage]),
      );

      try {
        const attachment = await uploadMedia(formData);
        const request: SendMessageRequest = {
          direction: "FAMILY_TO_HUB",
          message_type: params.mediaType,
          body: params.body ?? "",
          attachment_id: attachment.id,
          idempotency_key: idempotencyKey,
        };
        const saved = await sendMessage(elderId, request);
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
          deduplicateAndSort(
            prev.map((m) =>
              m.id === optimisticId || m.idempotency_key === idempotencyKey ? saved : m,
            ),
          ),
        );
        return saved;
      } catch (err) {
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
          prev.map((m) =>
            m.id === optimisticId ? { ...m, status: "FAILED" as const } : m,
          ),
        );
        throw err;
      }
    },
  });

  const retryMessage = useCallback(
    async (messageId: string) => {
      if (!elderId) return;
      const currentMessages = queryClient.getQueryData<Message[]>(messagesQueryKey) ?? [];
      const target = currentMessages.find((m) => m.id === messageId);
      if (!target || target.status !== "FAILED") return;

      queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
        prev.map((m) => (m.id === messageId ? { ...m, status: "PENDING" as const } : m)),
      );

      try {
        const request: SendMessageRequest = {
          direction: "FAMILY_TO_HUB",
          message_type: target.message_type,
          body: target.body,
          attachment_id: target.attachment?.id ?? null,
          idempotency_key: target.idempotency_key,
        };
        const saved = await sendMessage(elderId, request);
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
          deduplicateAndSort(prev.map((m) => (m.id === messageId ? saved : m))),
        );
        return saved;
      } catch (err) {
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev = []) =>
          prev.map((m) => (m.id === messageId ? { ...m, status: "FAILED" as const } : m)),
        );
        throw err;
      }
    },
    [elderId, messagesQueryKey, queryClient],
  );

  return {
    messages,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    markAsRead,
    retryMessage,
    sendTextMessage: sendTextMutation.mutateAsync,
    sendMediaMessage: sendMediaMutation.mutateAsync,
    isSending: sendTextMutation.isPending || sendMediaMutation.isPending,
  };
}
