import React from "react";
import { I18nManager, Image, Pressable, StyleSheet, View } from "react-native";
import { SvgXml } from "react-native-svg";
import { colors, radius, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { formatClock, t, toPersianDigits } from "../i18n";
import { getMediaDownloadUrl } from "../api/endpoints/messaging";
import type { Message } from "../api/types";

// WhatsApp vector ticks
const TICK_SENT_XML = `<svg width="13" height="11" viewBox="0 0 13 11" fill="none">
  <path d="M1.5 5.5L4.5 9L11.5 1.5" stroke="#8696A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`;

const TICK_DELIVERED_XML = `<svg width="17" height="11" viewBox="0 0 17 11" fill="none">
  <path d="M1.5 5.5L4.5 9L11.5 1.5" stroke="#8696A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M5.5 5.5L8.5 9L15.5 1.5" stroke="#8696A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`;

// Prominent, saturated WhatsApp Royal Blue for Read status
const TICK_READ_XML = `<svg width="17" height="11" viewBox="0 0 17 11" fill="none">
  <path d="M1.5 5.5L4.5 9L11.5 1.5" stroke="#0084FF" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M5.5 5.5L8.5 9L15.5 1.5" stroke="#0084FF" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`;

const MINI_MIC_XML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8696A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
  <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
  <line x1="12" y1="18" x2="12" y2="23"/>
</svg>`;

export type MessageBubbleProps = {
  message: Message;
  isPlayingVoice?: boolean;
  onPlayVoice?: (messageId: string) => void;
  onRetry?: (messageId: string) => void;
  onPressImage?: (imageUrl: string, caption?: string) => void;
  onPressVideo?: (videoUrl: string, caption?: string) => void;
  authToken?: string | null;
};

export function MessageBubble({
  message,
  isPlayingVoice = false,
  onPlayVoice,
  onRetry,
  onPressImage,
  onPressVideo,
  authToken,
}: MessageBubbleProps) {
  const isCaregiver = message.direction === "FAMILY_TO_HUB";

  const timeString = message.created_at
    ? toPersianDigits(formatClock(message.created_at))
    : "";

  const senderName = isCaregiver ? t.youSender : message.sender?.display_name;

  function renderStatusTicks() {
    if (!isCaregiver) return null;

    switch (message.status) {
      case "PENDING":
        return (
          <View style={styles.statusRow}>
            <AppText variant="caption" style={styles.tickPending}>🕒</AppText>
            <AppText variant="caption" style={styles.srOnly}>{t.statusPending}</AppText>
          </View>
        );
      case "SENT":
        return (
          <View style={styles.statusRow}>
            <SvgXml xml={TICK_SENT_XML} width={13} height={11} />
            <AppText variant="caption" style={styles.srOnly}>{t.statusSent}</AppText>
          </View>
        );
      case "DELIVERED":
        return (
          <View style={styles.statusRow}>
            <SvgXml xml={TICK_DELIVERED_XML} width={17} height={11} />
            <AppText variant="caption" style={styles.srOnly}>{t.statusDelivered}</AppText>
          </View>
        );
      case "READ":
        return (
          <View style={styles.statusRow}>
            <SvgXml xml={TICK_READ_XML} width={17} height={11} />
            <AppText variant="caption" style={styles.srOnly}>{t.statusRead}</AppText>
          </View>
        );
      case "FAILED":
        return (
          <Pressable
            onPress={() => onRetry?.(message.id)}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={`${t.statusFailed} - ${t.retry}`}
            style={styles.retryBadge}
          >
            <AppText variant="caption" color={colors.errorOn} style={styles.retryText}>
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
          <AppText variant="body" color="#111B21" style={styles.bodyText}>
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
            <AppText variant="caption" style={styles.srOnly}>
              {t.sendVoiceMessage}
            </AppText>

            <View style={styles.voiceRow}>
              <Pressable
                onPress={() => onPlayVoice?.(message.id)}
                style={styles.voicePlayButton}
                accessibilityRole="button"
                accessibilityLabel={isPlayingVoice ? t.voiceNotePause : t.voiceNotePlay}
              >
                <AppText variant="label" color="#FFFFFF" style={styles.voicePlayIcon}>
                  {isPlayingVoice ? "❚❚" : "▶"}
                </AppText>
              </Pressable>

              <View style={styles.voiceTrackContainer}>
                {/* Visual WhatsApp style wave line */}
                <View style={styles.waveformRow}>
                  <View style={[styles.waveDot, isPlayingVoice && styles.waveDotActive]} />
                  <View style={[styles.waveLine, { flex: 1 }]} />
                  <View style={[styles.waveDot, isPlayingVoice && styles.waveDotActive]} />
                </View>
                <View style={styles.voiceBottomRow}>
                  <AppText variant="caption" color="#667781" style={styles.voiceDuration}>
                    {durationText}
                  </AppText>
                  <View style={styles.voiceMicIcon}>
                    <SvgXml xml={MINI_MIC_XML} width={12} height={12} />
                  </View>
                </View>
              </View>
            </View>
            {message.body ? (
              <AppText variant="body" color="#111B21" style={styles.caption}>
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
              <Pressable
                onPress={() => onPressImage?.(imageUrl, message.body || undefined)}
                style={styles.imageThumbnailWrapper}
                accessibilityRole="button"
                accessibilityLabel={message.attachment?.original_filename || t.attachPhoto}
              >
                <Image
                  source={{ uri: imageUrl }}
                  style={styles.imageThumbnail}
                  resizeMode="cover"
                />
              </Pressable>
            ) : message.status === "PENDING" ? (
              <View style={styles.attachmentPlaceholder}>
                <AppText variant="caption" color="#667781">
                  ⏳ {t.uploadingMedia}
                </AppText>
              </View>
            ) : (
              <View style={styles.attachmentPlaceholder}>
                <AppText variant="caption" color="#667781">
                  📷 {message.attachment?.original_filename || t.attachPhoto}
                </AppText>
              </View>
            )}
            {message.body ? (
              <AppText variant="body" color="#111B21" style={styles.caption}>
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
        const videoUrl = message.attachment?.id
          ? getMediaDownloadUrl(message.attachment.id, authToken)
          : null;
        return (
          <View style={styles.mediaContainer}>
            {message.status === "PENDING" ? (
              <View style={styles.attachmentPlaceholder}>
                <AppText variant="caption" color="#667781">
                  ⏳ {t.uploadingMedia}
                </AppText>
              </View>
            ) : videoUrl ? (
              <Pressable
                onPress={() => onPressVideo?.(videoUrl, message.body || undefined)}
                style={styles.videoPreviewWrapper}
                accessibilityRole="button"
                accessibilityLabel={message.attachment?.original_filename || t.attachVideo}
              >
                <View style={styles.videoBackdrop}>
                  {/* Centered WhatsApp style play button */}
                  <View style={styles.videoPlayCircle}>
                    <AppText variant="label" color="#FFFFFF" style={styles.videoPlayIcon}>
                      ▶
                    </AppText>
                  </View>
                  <View style={styles.videoDurationPill}>
                    <AppText variant="caption" color="#FFFFFF" style={styles.videoDurationText}>
                      🎥 {message.attachment?.original_filename || ""} {durationText ? `(${durationText})` : ""}
                    </AppText>
                  </View>
                </View>
              </Pressable>
            ) : (
              <View style={styles.attachmentPlaceholder}>
                <AppText variant="caption" color="#667781">
                  🎥 {message.attachment?.original_filename || t.attachVideo}
                </AppText>
              </View>
            )}
            {message.body ? (
              <AppText variant="body" color="#111B21" style={styles.caption}>
                {message.body}
              </AppText>
            ) : null}
          </View>
        );
      }

      default:
        return (
          <AppText variant="body" color="#111B21" style={styles.bodyText}>
            {message.body}
          </AppText>
        );
    }
  }

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
        {/* Subtle sender name for incoming if display_name exists */}
        {!isCaregiver && senderName ? (
          <AppText variant="caption" color="#00A884" style={styles.senderHeader}>
            {senderName}
          </AppText>
        ) : isCaregiver ? (
          <AppText variant="caption" style={styles.srOnly}>
            {t.youSender}
          </AppText>
        ) : null}

        <View style={styles.contentContainer}>{renderMediaContent()}</View>

        <View style={styles.metaRow}>
          <AppText variant="caption" style={styles.metaTime}>
            {timeString}
          </AppText>
          {renderStatusTicks()}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bubbleWrapper: {
    marginVertical: 3,
    width: "100%",
    flexDirection: "row",
    paddingHorizontal: 10,
  },
  caregiverWrapper: {
    justifyContent: (typeof I18nManager !== "undefined" && I18nManager?.isRTL) ? "flex-start" : "flex-end", // User messages on RIGHT
  },
  hubWrapper: {
    justifyContent: (typeof I18nManager !== "undefined" && I18nManager?.isRTL) ? "flex-end" : "flex-start", // Contact messages on LEFT
  },
  bubble: {
    maxWidth: "84%",
    minWidth: 80,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: 6,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 1,
  },
  // WhatsApp Outgoing: Soft mint pastel green
  caregiverBubble: {
    backgroundColor: "#D9FDD3",
    borderBottomRightRadius: 3, // WhatsApp asymmetric tail anchor
    borderWidth: 0,
  },
  // WhatsApp Incoming: Crisp pure white
  hubBubble: {
    backgroundColor: "#FFFFFF",
    borderBottomLeftRadius: 3, // WhatsApp asymmetric tail anchor
    borderWidth: 1,
    borderColor: "#E9EDEF",
  },
  senderHeader: {
    fontSize: 12,
    fontWeight: "700",
    marginBottom: 2,
  },
  srOnly: {
    position: "absolute",
    width: 1,
    height: 1,
    opacity: 0.01,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#111B21",
  },
  contentContainer: {
    paddingVertical: 1,
  },
  metaRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
    alignItems: "center",
    gap: 4,
    marginTop: 2,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  metaTime: {
    fontSize: 11,
    color: "#667781",
  },
  tickPending: {
    fontSize: 11,
    color: "#667781",
  },
  tickSent: {
    fontSize: 13,
    color: "#8696A0",
    fontWeight: "600",
  },
  tickDelivered: {
    fontSize: 13,
    color: "#8696A0",
    fontWeight: "600",
  },
  // WhatsApp Blue Tick
  tickRead: {
    fontSize: 13,
    color: "#53BDEB",
    fontWeight: "700",
  },
  retryBadge: {
    backgroundColor: colors.errorSoft,
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: radius.sm,
  },
  retryText: {
    fontSize: 10,
    fontWeight: "600",
  },
  mediaContainer: {
    gap: 4,
  },
  voiceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 4,
    minWidth: 180,
  },
  voicePlayButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#00A884", // WhatsApp green
    justifyContent: "center",
    alignItems: "center",
  },
  voicePlayIcon: {
    fontSize: 13,
    marginLeft: 2,
  },
  voiceTrackContainer: {
    flex: 1,
    gap: 4,
  },
  waveformRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 2,
  },
  waveDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: "#8696A0",
  },
  waveDotActive: {
    backgroundColor: "#00A884",
  },
  waveLine: {
    height: 3,
    borderRadius: 1.5,
    backgroundColor: "#D1D7DB",
  },
  voiceBottomRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  voiceDuration: {
    fontSize: 11,
  },
  voiceMicIcon: {
    justifyContent: "center",
    alignItems: "center",
  },
  caption: {
    marginTop: 4,
    fontSize: 14,
    lineHeight: 20,
    color: "#111B21",
  },
  imageThumbnailWrapper: {
    width: 240,
    height: 170,
    borderRadius: 12,
    overflow: "hidden",
    position: "relative",
    backgroundColor: "#E2E8F0",
  },
  imageThumbnail: {
    width: "100%",
    height: "100%",
  },
  videoPreviewWrapper: {
    width: 240,
    height: 160,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#111B21",
  },
  videoBackdrop: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  },
  videoPlayCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "rgba(17, 27, 33, 0.65)",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: "rgba(255, 255, 255, 0.85)",
  },
  videoPlayIcon: {
    fontSize: 16,
    marginLeft: 3,
  },
  videoDurationPill: {
    position: "absolute",
    bottom: 6,
    left: 6,
    right: 6,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  videoDurationText: {
    fontSize: 11,
  },
  attachmentPlaceholder: {
    padding: spacing.sm,
    borderRadius: radius.sm,
    backgroundColor: "#F0F2F5",
    alignItems: "center",
    justifyContent: "center",
    minWidth: 160,
  },
});
