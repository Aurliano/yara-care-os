import React from "react";
import { Image, Pressable, StyleSheet, View } from "react-native";
import { colors, radius, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { Icon } from "./Icon";
import { formatClock, t, toPersianDigits } from "../i18n";
import { getMediaDownloadUrl } from "../api/endpoints/messaging";
import type { Message } from "../api/types";

export type MessageBubbleProps = {
  message: Message;
  isPlayingVoice?: boolean;
  onPlayVoice?: (messageId: string) => void;
  onRetry?: (messageId: string) => void;
  authToken?: string | null;
};

export function MessageBubble({
  message,
  isPlayingVoice = false,
  onPlayVoice,
  onRetry,
  authToken,
}: MessageBubbleProps) {
  const isCaregiver = message.direction === "FAMILY_TO_HUB";

  function renderDeliveryStatus() {
    if (!isCaregiver) return null;

    switch (message.status) {
      case "PENDING":
        return (
          <AppText variant="caption" color={colors.textSecondary}>
            {t.statusPending}
          </AppText>
        );
      case "SENT":
        return (
          <AppText variant="caption" color={colors.textSecondary}>
            ✓ {t.statusSent}
          </AppText>
        );
      case "DELIVERED":
        return (
          <AppText variant="caption" color={colors.textSecondary}>
            ✓✓ {t.statusDelivered}
          </AppText>
        );
      case "READ":
        return (
          <AppText variant="caption" color={colors.primary}>
            ✓✓ {t.statusRead}
          </AppText>
        );
      case "FAILED":
        return (
          <Pressable
            onPress={() => onRetry?.(message.id)}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={`${t.statusFailed} - ${t.retry}`}
            style={styles.retryButton}
          >
            <AppText variant="caption" color={colors.error}>
              ⚠ {t.statusFailed} ({t.retry})
            </AppText>
          </Pressable>
        );
      default:
        return null;
    }
  }

  function renderMediaContent() {
    switch (message.message_type) {
      case "TEXT":
        return (
          <AppText variant="body" color={colors.text}>
            {message.body}
          </AppText>
        );

      case "VOICE": {
        const duration = message.attachment?.duration_seconds ?? 0;
        const durationText =
          duration > 0
            ? `${toPersianDigits(Math.round(duration))} ${t.secondsShort}`
            : t.voiceNoteDuration;

        return (
          <View style={styles.mediaContainer}>
            <View style={styles.voiceRow}>
              <Pressable
                onPress={() => onPlayVoice?.(message.id)}
                style={[
                  styles.playButton,
                  { backgroundColor: isPlayingVoice ? colors.primary : colors.surfaceSoft },
                ]}
                accessibilityRole="button"
                accessibilityLabel={isPlayingVoice ? t.voiceNotePause : t.voiceNotePlay}
              >
                <AppText
                  variant="label"
                  color={isPlayingVoice ? colors.surface : colors.primary}
                >
                  {isPlayingVoice ? "❚❚" : "▶"}
                </AppText>
              </Pressable>
              <View style={styles.voiceInfo}>
                <AppText variant="label" color={colors.text}>
                  {t.sendVoiceMessage}
                </AppText>
                <AppText variant="caption" color={colors.textSecondary}>
                  {durationText}
                </AppText>
              </View>
            </View>
            {message.body ? (
              <AppText variant="body" color={colors.text} style={styles.caption}>
                {message.body}
              </AppText>
            ) : null}
          </View>
        );
      }

      case "IMAGE": {
        const imageUrl = message.attachment?.id
          ? getMediaDownloadUrl(message.attachment.id, authToken)
          : null;
        return (
          <View style={styles.mediaContainer}>
            {imageUrl ? (
              <Image
                source={{ uri: imageUrl }}
                style={styles.imageThumbnail}
                resizeMode="cover"
                accessibilityLabel={message.attachment?.original_filename || t.attachPhoto}
              />
            ) : (
              <View style={styles.attachmentCard}>
                <Icon name="chevron" color={colors.primary} width={18} height={18} />
                <View style={{ flex: 1 }}>
                  <AppText variant="label" color={colors.text}>
                    {message.attachment?.original_filename || t.attachPhoto}
                  </AppText>
                  <AppText variant="caption" color={colors.textSecondary}>
                    {t.attachPhoto}
                  </AppText>
                </View>
              </View>
            )}
            {message.body ? (
              <AppText variant="body" color={colors.text} style={styles.caption}>
                {message.body}
              </AppText>
            ) : null}
          </View>
        );
      }

      case "VIDEO": {
        const duration = message.attachment?.duration_seconds ?? 0;
        const durationText =
          duration > 0
            ? `${toPersianDigits(Math.round(duration))} ${t.secondsShort}`
            : "";
        return (
          <View style={styles.mediaContainer}>
            <View style={styles.attachmentCard}>
              <Icon name="chevron" color={colors.primary} width={18} height={18} />
              <View style={{ flex: 1 }}>
                <AppText variant="label" color={colors.text}>
                  {message.attachment?.original_filename || t.attachVideo}
                </AppText>
                <AppText variant="caption" color={colors.textSecondary}>
                  {durationText ? `${t.attachVideo} (${durationText})` : t.attachVideo}
                </AppText>
              </View>
            </View>
            {message.body ? (
              <AppText variant="body" color={colors.text} style={styles.caption}>
                {message.body}
              </AppText>
            ) : null}
          </View>
        );
      }

      default:
        return (
          <AppText variant="body" color={colors.text}>
            {message.body}
          </AppText>
        );
    }
  }

  const senderName = isCaregiver
    ? t.youSender
    : message.sender?.display_name || t.elderHubSender;

  const timeString = message.created_at
    ? toPersianDigits(formatClock(message.created_at))
    : "";

  return (
    <View
      style={[
        styles.bubbleWrapper,
        isCaregiver ? styles.caregiverWrapper : styles.hubWrapper,
      ]}
    >
      <View
        style={[
          styles.bubble,
          isCaregiver ? styles.caregiverBubble : styles.hubBubble,
        ]}
      >
        <View style={styles.headerRow}>
          <AppText
            variant="caption"
            color={isCaregiver ? colors.primary : colors.textSecondary}
          >
            {senderName}
          </AppText>
          <AppText variant="caption" color={colors.textSecondary}>
            {timeString}
          </AppText>
        </View>

        <View style={styles.contentContainer}>{renderMediaContent()}</View>

        <View style={styles.footerRow}>{renderDeliveryStatus()}</View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bubbleWrapper: {
    marginVertical: spacing.xs,
    width: "100%",
    flexDirection: "row",
  },
  caregiverWrapper: {
    justifyContent: "flex-end",
  },
  hubWrapper: {
    justifyContent: "flex-start",
  },
  bubble: {
    maxWidth: "85%",
    minWidth: 160,
    borderRadius: radius.md,
    padding: spacing.sm,
    borderWidth: 1,
    gap: spacing.xs,
  },
  caregiverBubble: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.primary,
  },
  hubBubble: {
    backgroundColor: colors.surface,
    borderColor: colors.borderStrong,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: 2,
  },
  contentContainer: {
    paddingVertical: 2,
  },
  footerRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
    alignItems: "center",
    marginTop: 2,
  },
  retryButton: {
    paddingVertical: 2,
    paddingHorizontal: 4,
  },
  mediaContainer: {
    gap: spacing.xs,
  },
  voiceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.xs,
  },
  playButton: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.primary,
  },
  voiceInfo: {
    flex: 1,
  },
  attachmentCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.background,
    padding: spacing.sm,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.borderStrong,
  },
  caption: {
    marginTop: spacing.xs,
  },
  imageThumbnail: {
    width: "100%",
    height: 180,
    borderRadius: radius.sm,
    backgroundColor: colors.surfaceSoft,
  },
});
