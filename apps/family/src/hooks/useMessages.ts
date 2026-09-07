import { useCallback, useEffect, useRef } from "react";
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

export function useMessages(elderId: string | null | undefined) {
  const queryClient = useQueryClient();
  const deliveredAcks = useRef<Set<string>>(new Set());

  const messagesQueryKey = elderId ? queryKeys.messages(elderId) : ["messages"];

  const query = useQuery({
    queryKey: messagesQueryKey,
    enabled: Boolean(elderId),
    queryFn: () => listMessages(elderId as string),
    refetchInterval: 3000,
  });

  const messages = query.data ?? [];

  // Automatically acknowledge delivery for incoming HUB_TO_FAMILY messages
  useEffect(() => {
    if (!messages.length) return;
    for (const msg of messages) {
      if (
        msg.direction === "HUB_TO_FAMILY" &&
        msg.status === "SENT" &&
        !deliveredAcks.current.has(msg.id)
      ) {
        deliveredAcks.current.add(msg.id);
        markMessageDelivered(msg.id).catch(() => {
          deliveredAcks.current.delete(msg.id);
        });
      }
    }
  }, [messages]);

  const markAsRead = useCallback(
    async (messageId: string) => {
      try {
        const updated = await markMessageRead(messageId);
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev) =>
          prev ? prev.map((m) => (m.id === messageId ? updated : m)) : [updated],
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

      queryClient.setQueryData<Message[]>(messagesQueryKey, (prev) => [
        ...(prev ?? []),
        optimisticMessage,
      ]);

      try {
        const saved = await sendMessage(elderId, request);
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev) =>
          prev ? prev.map((m) => (m.id === optimisticId ? saved : m)) : [saved],
        );
        return saved;
      } catch (err) {
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev) =>
          prev
            ? prev.map((m) =>
                m.id === optimisticId ? { ...m, status: "FAILED" as const } : m,
              )
            : [],
        );
        throw err;
      }
    },
  });

  const sendMediaMutation = useMutation({
    mutationFn: async (params: SendMediaParams) => {
      if (!elderId) throw new Error("Elder ID is required");

      const formData = new FormData();
      // Handle React Native vs Web FormData
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

      queryClient.setQueryData<Message[]>(messagesQueryKey, (prev) => [
        ...(prev ?? []),
        optimisticMessage,
      ]);

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
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev) =>
          prev ? prev.map((m) => (m.id === optimisticId ? saved : m)) : [saved],
        );
        return saved;
      } catch (err) {
        queryClient.setQueryData<Message[]>(messagesQueryKey, (prev) =>
          prev
            ? prev.map((m) =>
                m.id === optimisticId ? { ...m, status: "FAILED" as const } : m,
              )
            : [],
        );
        throw err;
      }
    },
  });

  return {
    messages,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    markAsRead,
    sendTextMessage: sendTextMutation.mutateAsync,
    sendMediaMessage: sendMediaMutation.mutateAsync,
    isSending: sendTextMutation.isPending || sendMediaMutation.isPending,
  };
}
