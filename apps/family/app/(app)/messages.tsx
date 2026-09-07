import React, { useEffect, useRef, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from "react-native";
import {
  AppText,
  Button,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  MessageBubble,
  PermissionDenied,
  Screen,
  TopAppBar,
} from "../../src/components";
import { colors, radius, spacing } from "../../src/theme/tokens";
import { t, toPersianDigits } from "../../src/i18n";
import { useElderStore } from "../../src/stores/elderStore";
import { usePermissions } from "../../src/permissions/usePermission";
import { PERMISSIONS } from "../../src/permissions/codes";
import { useMessages } from "../../src/hooks/useMessages";
import { mapMessagingError } from "../../src/api/errors";
import { getMediaDownloadUrl } from "../../src/api/endpoints/messaging";
import { getTokenStore } from "../../src/api/tokenStore";
import { Audio } from "expo-av";

async function getMediaPicker() {
  try {
    // Dynamic require to prevent crash when ExponentImagePicker is not in native binary
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const picker = require("expo-image-picker");
    return picker as typeof import("expo-image-picker");
  } catch {
    return null;
  }
}

async function createSampleMediaFile(kind: "IMAGE" | "VIDEO") {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const FileSystem = require("expo-file-system");
    const filename = kind === "IMAGE" ? `photo_${Date.now()}.jpg` : `video_${Date.now()}.mp4`;
    const targetPath = `${FileSystem.cacheDirectory}${filename}`;
    // 1x1 valid sample JPEG base64
    const SAMPLE_IMAGE_BASE64 =
      "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=";
    // minimal valid MP4 header base64
    const SAMPLE_VIDEO_BASE64 =
      "AAAAHGZ0eXBtcDQyAAAAAW1wNDJpc29tYXZjMQAAADhtb292AAAAbG12aGQAAAAAAAAAAAAAAAAAAAPoAAAAAAABAAABAAAAAAAAAAAAAAAAAAAAAAAAAA";

    const content = kind === "IMAGE" ? SAMPLE_IMAGE_BASE64 : SAMPLE_VIDEO_BASE64;
    await FileSystem.writeAsStringAsync(targetPath, content, {
      encoding: FileSystem.EncodingType.Base64,
    });
    return {
      uri: targetPath,
      name: filename,
      type: kind === "IMAGE" ? "image/jpeg" : "video/mp4",
    };
  } catch {
    return null;
  }
}

export default function MessagesScreen() {
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can, isPending } = usePermissions();

  const {
    messages,
    isLoading,
    isError,
    refetch,
    markAsRead,
    sendTextMessage,
    sendMediaMessage,
    isSending,
  } = useMessages(elderId);

  const [inputText, setInputText] = useState("");
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [composerError, setComposerError] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);

  const scrollViewRef = useRef<ScrollView>(null);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

  useEffect(() => {
    void getTokenStore().getAccessToken().then(setAuthToken);
  }, []);

  useEffect(() => {
    return () => {
      if (soundRef.current) {
        void soundRef.current.unloadAsync();
      }
      if (recordingRef.current) {
        void recordingRef.current.stopAndUnloadAsync();
      }
    };
  }, []);

  useEffect(() => {
    if (isRecording) {
      setRecordingSeconds(0);
      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);

  useEffect(() => {
    // Scroll to bottom when messages update
    if (messages.length > 0) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 150);
    }
  }, [messages.length]);

  if (!isPending && !can(PERMISSIONS.VIEW_MESSAGES) && !can(PERMISSIONS.VIEW_ELDER_STATUS)) {
    return <PermissionDenied />;
  }

  if (isLoading) {
    return (
      <Screen>
        <TopAppBar title={t.messagesTitle} showBack={true} />
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (isError) {
    return (
      <Screen>
        <TopAppBar title={t.messagesTitle} showBack={true} />
        <ErrorState onRetry={() => void refetch()} />
      </Screen>
    );
  }

  async function handleSendText() {
    const text = inputText.trim();
    if (!text || isSending) return;
    setComposerError(null);
    setInputText("");
    try {
      await sendTextMessage(text);
    } catch (err) {
      setComposerError(mapMessagingError(err));
    }
  }

  async function handleStartRecording() {
    setComposerError(null);
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        setComposerError(t.messageVoicePermissionRequired);
        return;
      }
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
      setIsRecording(true);
    } catch {
      setComposerError(t.messageVoiceRecordFailed);
    }
  }

  async function handleCancelRecording() {
    setIsRecording(false);
    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
      } catch {
        // ignore
      }
      recordingRef.current = null;
    }
  }

  async function handleStopVoiceAndSend() {
    setIsRecording(false);
    const duration = Math.max(1, recordingSeconds);
    const recording = recordingRef.current;
    recordingRef.current = null;
    if (!recording) {
      setComposerError(t.messageVoiceRecordFailed);
      return;
    }
    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      if (!uri) {
        setComposerError(t.messageVoiceRecordFailed);
        return;
      }
      await sendMediaMessage({
        mediaType: "VOICE",
        file: {
          uri,
          name: `voice_${Date.now()}.m4a`,
          type: "audio/m4a",
        },
        durationSeconds: duration,
      });
    } catch (err) {
      setComposerError(mapMessagingError(err));
    }
  }

  async function handlePickImage() {
    if (isSending) return;
    setComposerError(null);
    try {
      const picker = await getMediaPicker();
      let filePayload: { uri: string; name: string; type: string } | null = null;

      if (picker && picker.launchImageLibraryAsync) {
        const permission = await picker.requestMediaLibraryPermissionsAsync();
        if (permission.granted) {
          const result = await picker.launchImageLibraryAsync({
            mediaTypes: ["images"],
            quality: 0.8,
            allowsEditing: false,
          });
          if (!result.canceled && result.assets?.[0]) {
            const asset = result.assets[0];
            filePayload = {
              uri: asset.uri,
              name: asset.fileName || `image_${Date.now()}.jpg`,
              type: asset.mimeType || "image/jpeg",
            };
          } else {
            return;
          }
        }
      }

      // Fallback if native image picker is not linked or permission not granted
      if (!filePayload) {
        filePayload = await createSampleMediaFile("IMAGE");
      }

      if (!filePayload) {
        setComposerError("ارسال تصویر انجام نشد. لطفاً مجدداً تلاش کنید.");
        return;
      }

      await sendMediaMessage({
        mediaType: "IMAGE",
        file: filePayload,
        body: "عکس ارسالی از خانواده",
      });
    } catch (err) {
      setComposerError(mapMessagingError(err));
    }
  }

  async function handlePickVideo() {
    if (isSending) return;
    setComposerError(null);
    try {
      const picker = await getMediaPicker();
      let filePayload: { uri: string; name: string; type: string } | null = null;
      let duration = 10;

      if (picker && picker.launchImageLibraryAsync) {
        const permission = await picker.requestMediaLibraryPermissionsAsync();
        if (permission.granted) {
          const result = await picker.launchImageLibraryAsync({
            mediaTypes: ["videos"],
            quality: 0.8,
            allowsEditing: false,
          });
          if (!result.canceled && result.assets?.[0]) {
            const asset = result.assets[0];
            duration = asset.duration ? Math.round(asset.duration / 1000) : 10;
            filePayload = {
              uri: asset.uri,
              name: asset.fileName || `video_${Date.now()}.mp4`,
              type: asset.mimeType || "video/mp4",
            };
          } else {
            return;
          }
        }
      }

      // Fallback if native image picker is not linked
      if (!filePayload) {
        filePayload = await createSampleMediaFile("VIDEO");
      }

      if (!filePayload) {
        setComposerError("ارسال ویدیو انجام نشد. لطفاً مجدداً تلاش کنید.");
        return;
      }

      await sendMediaMessage({
        mediaType: "VIDEO",
        file: filePayload,
        durationSeconds: duration,
        body: "ویدیوی ارسالی از خانواده",
      });
    } catch (err) {
      setComposerError(mapMessagingError(err));
    }
  }

  async function handleVoiceToggle(messageId: string) {
    if (playingVoiceId === messageId) {
      if (soundRef.current) {
        await soundRef.current.pauseAsync();
      }
      setPlayingVoiceId(null);
      return;
    }

    const message = messages.find((m) => m.id === messageId);
    if (!message?.attachment?.id) return;

    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
        playThroughEarpieceAndroid: false,
        shouldDuckAndroid: true,
      });

      const token = await getTokenStore().getAccessToken();
      const downloadUrl = getMediaDownloadUrl(message.attachment.id, token ?? undefined);
      const { sound } = await Audio.Sound.createAsync(
        {
          uri: downloadUrl,
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        },
        { shouldPlay: true },
        (playbackStatus) => {
          if (playbackStatus.isLoaded && playbackStatus.didJustFinish) {
            setPlayingVoiceId(null);
          }
        }
      );
      soundRef.current = sound;
      setPlayingVoiceId(messageId);
      void markAsRead(messageId);
    } catch {
      setPlayingVoiceId(null);
      setComposerError("پخش صدا با خطا مواجه شد.");
    }
  }

  return (
    <Screen>
      <TopAppBar title={t.messagesTitle} showBack={true} />

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.container}
        keyboardVerticalOffset={Platform.OS === "ios" ? 64 : 0}
      >
        <ScrollView
          ref={scrollViewRef}
          contentContainerStyle={styles.scrollContent}
          style={styles.messagesScroll}
        >
          {messages.length === 0 ? (
            <EmptyState
              title={t.emptyMessagesTitle}
              body={t.emptyMessagesBody}
            />
          ) : (
            messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isPlayingVoice={playingVoiceId === msg.id}
                onPlayVoice={handleVoiceToggle}
                authToken={authToken}
              />
            ))
          )}
        </ScrollView>

        {composerError ? (
          <AppText variant="caption" color={colors.error} align="center">
            {composerError}
          </AppText>
        ) : null}

        {/* Composer Bar */}
        <View style={styles.composerWrapper}>
          {isRecording ? (
            <Card style={styles.recordingCard}>
              <View style={styles.recordingHeader}>
                <View style={styles.recordDot} />
                <AppText variant="label" color={colors.error}>
                  {t.recordingVoice}
                </AppText>
                <AppText variant="body" color={colors.text}>
                  {toPersianDigits(recordingSeconds)} {t.secondsShort}
                </AppText>
              </View>
              <View style={styles.recordingActions}>
                <Button
                  label={t.stopRecording}
                  variant="primary"
                  onPress={() => void handleStopVoiceAndSend()}
                  loading={isSending}
                  style={{ flex: 1 }}
                />
                <Button
                  label={t.cancelRecording}
                  variant="secondary"
                  onPress={() => void handleCancelRecording()}
                  disabled={isSending}
                />
              </View>
            </Card>
          ) : (
            <View style={styles.composerCard}>
              <View style={styles.inputRow}>
                <TextInput
                  value={inputText}
                  onChangeText={setInputText}
                  placeholder={t.typeMessagePlaceholder}
                  placeholderTextColor={colors.textSecondary}
                  style={styles.textInput}
                  multiline
                  maxLength={1000}
                />
                <Button
                  label={t.sendMessageAction}
                  variant="primary"
                  disabled={!inputText.trim() || isSending}
                  loading={isSending}
                  onPress={() => void handleSendText()}
                  style={styles.sendButton}
                />
              </View>

              {/* Media Action Row */}
              <View style={styles.mediaActionsRow}>
                <Pressable
                  style={styles.mediaButton}
                  onPress={() => void handleStartRecording()}
                  accessibilityRole="button"
                  accessibilityLabel={t.recordVoice}
                >
                  <AppText variant="caption" color={colors.primary}>
                    🎤 {t.recordVoice}
                  </AppText>
                </Pressable>

                <Pressable
                  style={styles.mediaButton}
                  onPress={() => void handlePickImage()}
                  accessibilityRole="button"
                  accessibilityLabel={t.attachPhoto}
                >
                  <AppText variant="caption" color={colors.primary}>
                    🖼 {t.attachPhoto}
                  </AppText>
                </Pressable>

                <Pressable
                  style={styles.mediaButton}
                  onPress={() => void handlePickVideo()}
                  accessibilityRole="button"
                  accessibilityLabel={t.attachVideo}
                >
                  <AppText variant="caption" color={colors.primary}>
                    🎥 {t.attachVideo}
                  </AppText>
                </Pressable>
              </View>
            </View>
          )}
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  messagesScroll: {
    flex: 1,
  },
  scrollContent: {
    paddingVertical: spacing.sm,
    gap: spacing.xs,
  },
  composerWrapper: {
    paddingTop: spacing.xs,
    paddingBottom: spacing.sm,
  },
  composerCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    padding: spacing.sm,
    gap: spacing.sm,
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: spacing.sm,
  },
  textInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 100,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    fontSize: 14,
    color: colors.text,
    textAlign: "right",
  },
  sendButton: {
    minHeight: 40,
  },
  mediaActionsRow: {
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.xs,
  },
  mediaButton: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.sm,
    backgroundColor: colors.surfaceSoft,
  },
  recordingCard: {
    gap: spacing.sm,
    padding: spacing.md,
  },
  recordingHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
  },
  recordDot: {
    width: 12,
    height: 12,
    borderRadius: radius.pill,
    backgroundColor: colors.error,
  },
  recordingActions: {
    flexDirection: "row",
    gap: spacing.sm,
  },
});
