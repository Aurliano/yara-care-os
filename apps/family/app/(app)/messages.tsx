import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Image,
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  TextInput,
  View,
} from "react-native";
import { SvgXml } from "react-native-svg";
import {
  AppText,
  Avatar,
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
import { formatClock, t, toPersianDigits } from "../../src/i18n";
import { useElderStore } from "../../src/stores/elderStore";
import { usePermissions } from "../../src/permissions/usePermission";
import { PERMISSIONS } from "../../src/permissions/codes";
import { useMessages } from "../../src/hooks/useMessages";
import { mapMessagingError } from "../../src/api/errors";
import { getMediaDownloadUrl } from "../../src/api/endpoints/messaging";
import { listContacts } from "../../src/api/endpoints/communication";
import { getElder } from "../../src/api/endpoints/identity";
import { queryKeys } from "../../src/api/queryKeys";
import { getTokenStore } from "../../src/api/tokenStore";
import { useQuery } from "@tanstack/react-query";
import { Audio, ResizeMode, Video } from "expo-av";

// Sleek minimal vector icons
const ATTACH_ICON_XML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#54656F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
</svg>`;

const MIC_ICON_XML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
  <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
  <line x1="12" y1="18" x2="12" y2="23"/>
  <line x1="8" y1="23" x2="16" y2="23"/>
</svg>`;

const SEND_ICON_XML = `<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="22" y1="2" x2="11" y2="13"/>
  <polygon points="22 2 15 22 11 13 2 9 22 2" fill="#FFFFFF"/>
</svg>`;

// Back arrow pointing right (→) for Persian RTL WhatsApp navigation
const BACK_ARROW_RTL_XML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#111B21" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
  <line x1="5" y1="12" x2="19" y2="12"/>
  <polyline points="12 5 19 12 12 19"/>
</svg>`;

async function getMediaPicker() {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const picker = require("expo-image-picker");
    return picker as typeof import("expo-image-picker");
  } catch {
    return null;
  }
}

const QUICK_REPLIES = ["سلام", "خوب هستید؟", "داروها مصرف شد؟", "تماس می‌گیرم"];

export default function MessagesScreen() {
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can, isPending } = usePermissions();

  const elderQuery = useQuery({
    queryKey: elderId ? queryKeys.elder(elderId) : ["elder"],
    enabled: Boolean(elderId) && can(PERMISSIONS.VIEW_ELDER_STATUS),
    queryFn: () => getElder(elderId as string),
  });

  const contactsQuery = useQuery({
    queryKey: elderId ? queryKeys.contacts(elderId) : ["contacts"],
    enabled: Boolean(elderId) && can(PERMISSIONS.VIEW_ELDER_STATUS),
    queryFn: () => listContacts(elderId as string),
  });

  // Explicitly disable autoMarkRead on the list level so unread counts persist
  const {
    messages,
    isLoading: isMessagesLoading,
    isError: isMessagesError,
    refetch: refetchMessages,
    markAsRead,
    sendTextMessage,
    sendMediaMessage,
    retryMessage,
    isSending,
  } = useMessages(elderId, { autoMarkRead: false });

  const elderName = elderQuery.data?.full_name || "سالمند";

  // Target chat: either the elder's conversation (default) or a specific contact
  const [selectedChat, setSelectedChat] = useState<{
    id: string;
    title: string;
    subtitle: string;
    isElder: boolean;
    photoUrl?: string | null;
  } | null>(null);

  const [inputText, setInputText] = useState("");
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [composerError, setComposerError] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [pendingAttachment, setPendingAttachment] = useState<{
    uri: string;
    name: string;
    type: string;
    mediaType: "IMAGE" | "VIDEO";
    durationSeconds?: number;
  } | null>(null);
  const [attachmentCaption, setAttachmentCaption] = useState("");
  const [viewerMedia, setViewerMedia] = useState<{
    type: "IMAGE" | "VIDEO";
    url: string;
    caption?: string;
  } | null>(null);

  const [keyboardOffset, setKeyboardOffset] = useState(0);

  const scrollViewRef = useRef<ScrollView>(null);
  const isNearBottomRef = useRef(true);
  const prevMsgCountRef = useRef(0);
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

  // Listen to keyboard show/hide to reliably move bottom composer above Android & iOS keyboard
  useEffect(() => {
    const onShow = (e: any) => {
      const height = e.endCoordinates?.height ?? 0;
      if (Platform.OS === "android") {
        setKeyboardOffset(height);
      }
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 60);
    };
    const onHide = () => {
      if (Platform.OS === "android") {
        setKeyboardOffset(0);
      }
    };

    const showSub = Keyboard.addListener(
      Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow",
      onShow,
    );
    const hideSub = Keyboard.addListener(
      Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide",
      onHide,
    );

    return () => {
      showSub.remove();
      hideSub.remove();
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

  // All messages in /elders/{elderId}/messages/ are the conversation with the Elder's Hub
  const conversationMessages = messages;

  // Unread incoming count
  const unreadCount = useMemo(() => {
    return messages.filter(
      (m) => m.direction === "HUB_TO_FAMILY" && m.status !== "READ",
    ).length;
  }, [messages]);

  // Mark unread incoming messages as read ONLY when user is inside the conversation
  useEffect(() => {
    if (selectedChat) {
      conversationMessages
        .filter((m) => m.direction === "HUB_TO_FAMILY" && m.status !== "READ")
        .forEach((m) => void markAsRead(m.id));
    }
  }, [conversationMessages, selectedChat, markAsRead]);

  // Auto-scroll logic: scroll to bottom on entry or when near bottom and new message arrives
  useEffect(() => {
    if (!selectedChat) return;
    const count = conversationMessages.length;
    const isNew = count > prevMsgCountRef.current;
    prevMsgCountRef.current = count;

    if (count > 0) {
      if (isNearBottomRef.current || !isNew) {
        setTimeout(() => {
          scrollViewRef.current?.scrollToEnd({ animated: isNew });
        }, 100);
      }
    }
  }, [conversationMessages.length, selectedChat]);

  const handleScroll = (event: any) => {
    const { layoutMeasurement, contentOffset, contentSize } = event.nativeEvent;
    const paddingToBottom = 60;
    const isClose =
      layoutMeasurement.height + contentOffset.y >= contentSize.height - paddingToBottom;
    isNearBottomRef.current = isClose;
  };

  if (!isPending && !can(PERMISSIONS.VIEW_MESSAGES) && !can(PERMISSIONS.VIEW_ELDER_STATUS)) {
    return <PermissionDenied />;
  }

  if (elderQuery.isLoading || (selectedChat && isMessagesLoading)) {
    return (
      <Screen>
        <TopAppBar title={t.messagesTitle} showBack={true} />
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (elderQuery.isError || (selectedChat && isMessagesError)) {
    return (
      <Screen>
        <TopAppBar title={t.messagesTitle} showBack={true} />
        <ErrorState
          onRetry={() => {
            void elderQuery.refetch();
            void contactsQuery.refetch();
            void refetchMessages();
          }}
        />
      </Screen>
    );
  }

  async function handleSendText(textToSend?: string) {
    const text = (textToSend ?? inputText).trim();
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
        Audio.RecordingOptionsPresets.HIGH_QUALITY,
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
    setShowAttachMenu(false);
    if (isSending) return;
    setComposerError(null);
    try {
      const picker = await getMediaPicker();
      if (picker && picker.launchImageLibraryAsync) {
        const result = await picker.launchImageLibraryAsync({
          mediaTypes: picker.MediaTypeOptions.Images,
          quality: 0.8,
        });
        if (!result.canceled && result.assets && result.assets.length > 0) {
          const asset = result.assets[0];
          const filename = asset.fileName || `photo_${Date.now()}.jpg`;
          const ext = filename.split(".").pop()?.toLowerCase();
          const mimeType = ext === "png" ? "image/png" : ext === "webp" ? "image/webp" : "image/jpeg";
          setPendingAttachment({
            uri: asset.uri,
            name: filename,
            type: mimeType,
            mediaType: "IMAGE",
          });
          setAttachmentCaption("");
        }
      }
    } catch {
      setComposerError(t.attachPhotoFailed);
    }
  }

  async function handlePickVideo() {
    setShowAttachMenu(false);
    if (isSending) return;
    setComposerError(null);
    try {
      const picker = await getMediaPicker();
      if (picker && picker.launchImageLibraryAsync) {
        const result = await picker.launchImageLibraryAsync({
          mediaTypes: picker.MediaTypeOptions.Videos,
          quality: 0.8,
        });
        if (!result.canceled && result.assets && result.assets.length > 0) {
          const asset = result.assets[0];
          const filename = asset.fileName || `video_${Date.now()}.mp4`;
          setPendingAttachment({
            uri: asset.uri,
            name: filename,
            type: "video/mp4",
            mediaType: "VIDEO",
            durationSeconds: asset.duration ? Math.round(asset.duration / 1000) : undefined,
          });
          setAttachmentCaption("");
        }
      }
    } catch {
      setComposerError(t.attachVideoFailed);
    }
  }

  async function handleSendPendingAttachment() {
    if (!pendingAttachment || isSending) return;
    setComposerError(null);
    const attachment = pendingAttachment;
    const caption = attachmentCaption.trim() || undefined;
    setPendingAttachment(null);
    setAttachmentCaption("");

    try {
      await sendMediaMessage({
        mediaType: attachment.mediaType,
        file: {
          uri: attachment.uri,
          name: attachment.name,
          type: attachment.type,
        },
        durationSeconds: attachment.durationSeconds,
        body: caption,
      });
    } catch (err) {
      setComposerError(mapMessagingError(err));
    }
  }

  function handleCancelPendingAttachment() {
    setPendingAttachment(null);
    setAttachmentCaption("");
  }

  async function handleVoiceToggle(messageId: string) {
    if (playingVoiceId === messageId) {
      if (soundRef.current) {
        await soundRef.current.stopAsync();
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
      setPlayingVoiceId(null);
      return;
    }

    const targetMsg = messages.find((m) => m.id === messageId);
    if (!targetMsg || !targetMsg.attachment?.id) return;

    try {
      if (soundRef.current) {
        await soundRef.current.stopAsync();
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }

      const mediaUrl = getMediaDownloadUrl(targetMsg.attachment.id, authToken);
      const { sound } = await Audio.Sound.createAsync(
        { uri: mediaUrl },
        { shouldPlay: true },
        (status) => {
          if (status.isLoaded && status.didJustFinish) {
            setPlayingVoiceId(null);
          }
        },
      );
      soundRef.current = sound;
      setPlayingVoiceId(messageId);
      void markAsRead(messageId);
    } catch {
      setPlayingVoiceId(null);
      setComposerError("پخش صدا با خطا مواجه شد.");
    }
  }

  // ==========================================
  // VIEW 1: CONTACT / CONVERSATION LIST (WhatsApp Style)
  // ==========================================
  if (!selectedChat) {
    const lastMsg = messages.length > 0 ? messages[messages.length - 1] : null;
    const lastMsgSnippet = lastMsg
      ? lastMsg.message_type === "TEXT"
        ? lastMsg.body
        : lastMsg.message_type === "IMAGE"
        ? "📷 عکس"
        : lastMsg.message_type === "VIDEO"
        ? "🎥 ویدیو"
        : "🎙️ پیام صوتی"
      : "ارتباط مستقیم با تبلت یارا";

    const lastMsgTime = lastMsg?.created_at
      ? toPersianDigits(formatClock(lastMsg.created_at))
      : "";

    const contacts = contactsQuery.data ?? [];

    return (
      <Screen>
        <TopAppBar title={t.messagesTitle} showBack={true} />

        <ScrollView contentContainerStyle={styles.chatListScroll}>
          {/* Section: Active Conversation with Elder */}
          <View style={styles.sectionHeaderRow}>
            <AppText variant="caption" color={colors.textSecondary} style={styles.sectionHeader}>
              گفتگوهای فعال
            </AppText>
          </View>

          {/* WhatsApp Style Elder Conversation Item */}
          <Pressable
            style={styles.chatListItem}
            onPress={() => {
              setSelectedChat({
                id: "elder",
                title: elderName,
                subtitle: "تبلت یارا • آنلاین",
                isElder: true,
              });
              isNearBottomRef.current = true;
            }}
            accessibilityRole="button"
            accessibilityLabel={`گفتگو با ${elderName}`}
          >
            <View style={styles.avatarWrapper}>
              <Avatar name={elderName} size={52} />
              <View style={styles.onlineDot} />
            </View>

            <View style={styles.chatItemBody}>
              <View style={styles.chatItemTopRow}>
                <AppText variant="label" style={styles.chatItemTitle}>
                  {elderName}
                </AppText>
                {lastMsgTime ? (
                  <AppText variant="caption" color={unreadCount > 0 ? "#00A884" : "#8696A0"}>
                    {lastMsgTime}
                  </AppText>
                ) : null}
              </View>

              <View style={styles.chatItemBottomRow}>
                <AppText
                  variant="caption"
                  color={unreadCount > 0 ? "#111B21" : colors.textSecondary}
                  style={[styles.chatSnippet, unreadCount > 0 && styles.chatSnippetUnread]}
                  numberOfLines={1}
                >
                  {lastMsgSnippet}
                </AppText>

                {unreadCount > 0 ? (
                  <View style={styles.whatsappUnreadBadge}>
                    <AppText variant="caption" color="#FFFFFF" style={styles.unreadBadgeText}>
                      {toPersianDigits(unreadCount)}
                    </AppText>
                  </View>
                ) : null}
              </View>
            </View>
          </Pressable>

          {/* Section: Other Registered Contacts on Hub */}
          {contacts.length > 0 ? (
            <>
              <View style={[styles.sectionHeaderRow, { marginTop: 16 }]}>
                <AppText variant="caption" color={colors.textSecondary} style={styles.sectionHeader}>
                  مخاطبان ثبت‌شده در تبلت سالمند
                </AppText>
              </View>

              {contacts.map((contact) => {
                const photoUrl = contact.photo_reference
                  ? getMediaDownloadUrl(contact.photo_reference, authToken)
                  : null;

                return (
                  <Pressable
                    key={contact.id}
                    style={styles.contactItem}
                    onPress={() => {
                      setSelectedChat({
                        id: contact.id,
                        title: elderName, // Chat target is always Elder Hub
                        subtitle: `ارتباط پیام و تبلت • به عنوان ${contact.display_name}`,
                        isElder: false,
                        photoUrl,
                      });
                      isNearBottomRef.current = true;
                    }}
                    accessibilityRole="button"
                    accessibilityLabel={`گفتگو با ${elderName} به نام ${contact.display_name}`}
                  >
                    <Avatar name={contact.display_name} photoUrl={photoUrl} size={44} />
                    <View style={styles.contactInfo}>
                      <View style={styles.contactHeaderRow}>
                        <AppText variant="label" style={styles.contactName}>
                          {contact.display_name}
                        </AppText>
                        {contact.is_priority ? (
                          <View style={styles.priorityBadge}>
                            <AppText variant="caption" color={colors.primary} style={styles.priorityText}>
                              مخاطب اصلی هاب
                            </AppText>
                          </View>
                        ) : null}
                      </View>
                      <AppText variant="caption" color={colors.textSecondary} style={styles.contactPhone}>
                        {contact.phone || "مخاطب تبلت یارا"}
                      </AppText>
                    </View>
                    <AppText variant="label" color="#8696A0" style={styles.chevron}>
                      ›
                    </AppText>
                  </Pressable>
                );
              })}
            </>
          ) : null}
        </ScrollView>
      </Screen>
    );
  }

  // ==========================================
  // VIEW 2: CONVERSATION WITH ELDER (WhatsApp Style)
  // ==========================================
  return (
    <View style={styles.conversationContainer}>
      {/* 1. Sleek Minimal WhatsApp Header with proper Android status bar spacing */}
      <View style={styles.whatsappHeader}>
        <Pressable
          onPress={() => setSelectedChat(null)}
          style={styles.backButton}
          hitSlop={12}
          accessibilityRole="button"
          accessibilityLabel="بازگشت"
        >
          <SvgXml xml={BACK_ARROW_RTL_XML} width={24} height={24} />
        </Pressable>

        <Pressable
          onPress={() => setSelectedChat(null)}
          style={styles.headerInfoGroup}
          accessibilityRole="button"
          accessibilityLabel={`پروفایل ${selectedChat.title}`}
        >
          <View style={styles.headerAvatarWrapper}>
            <Avatar
              name={selectedChat.title}
              photoUrl={selectedChat.photoUrl}
              size={42}
            />
            <View style={styles.headerOnlineDot} />
          </View>

          <View style={styles.headerTitles}>
            <AppText variant="label" style={styles.headerName} numberOfLines={1}>
              {selectedChat.title}
            </AppText>
            <AppText variant="caption" color="#00A884" style={styles.headerStatus} numberOfLines={1}>
              {selectedChat.subtitle}
            </AppText>
          </View>
        </Pressable>
      </View>

      {/* 2. Scrollable Message List (Flex 1) */}
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.messagesFlexContainer}
        keyboardVerticalOffset={Platform.OS === "ios" ? 80 : 0}
      >
        <ScrollView
          ref={scrollViewRef}
          onScroll={handleScroll}
          scrollEventThrottle={16}
          style={styles.messagesScroll}
          contentContainerStyle={styles.messagesScrollContent}
        >
          {conversationMessages.length === 0 ? (
            <EmptyState
              title={t.emptyMessagesTitle}
              body={t.emptyMessagesBody}
            />
          ) : (
            <>
              {conversationMessages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  isPlayingVoice={playingVoiceId === msg.id}
                  onPlayVoice={handleVoiceToggle}
                  onRetry={(id) => void retryMessage(id)}
                  onPressImage={(url, caption) => setViewerMedia({ type: "IMAGE", url, caption })}
                  onPressVideo={(url, caption) => setViewerMedia({ type: "VIDEO", url, caption })}
                  authToken={authToken}
                />
              ))}
            </>
          )}
        </ScrollView>

        {composerError ? (
          <View style={styles.errorBanner}>
            <AppText variant="caption" color={colors.error} align="center">
              {composerError}
            </AppText>
          </View>
        ) : null}

        {/* 3. Fixed Bottom Composer - Elevated above Android & iOS keyboard */}
        <View
          style={[
            styles.fixedComposer,
            Platform.OS === "android" && keyboardOffset > 0 && {
              paddingBottom: keyboardOffset + 8,
            },
          ]}
        >
          {/* Pending Attachment Card */}
          {pendingAttachment ? (
            <Card style={styles.previewCard}>
              <View style={styles.previewHeader}>
                <AppText variant="caption" color={colors.primary}>
                  پیش‌نمایش {pendingAttachment.mediaType === "IMAGE" ? "عکس" : "ویدیو"}
                </AppText>
                <Pressable onPress={handleCancelPendingAttachment} hitSlop={8}>
                  <AppText variant="caption" color={colors.error}>
                    ✕ انصراف
                  </AppText>
                </Pressable>
              </View>

              <View style={styles.previewContentRow}>
                {pendingAttachment.mediaType === "IMAGE" ? (
                  <Image source={{ uri: pendingAttachment.uri }} style={styles.previewThumbnail} />
                ) : (
                  <View style={[styles.previewThumbnail, styles.videoPreviewFallback]}>
                    <AppText variant="caption" color="#FFFFFF">
                      🎥 ویدیو
                    </AppText>
                  </View>
                )}
                <View style={styles.previewDetails}>
                  <TextInput
                    value={attachmentCaption}
                    onChangeText={setAttachmentCaption}
                    placeholder="توضیح دلخواه بنویسید..."
                    placeholderTextColor="#8696A0"
                    style={styles.captionInput}
                    maxLength={300}
                  />
                </View>
              </View>

              <View style={styles.previewActions}>
                <Button
                  label="ارسال فایل"
                  variant="primary"
                  onPress={() => void handleSendPendingAttachment()}
                  loading={isSending}
                  style={{ flex: 1 }}
                />
              </View>
            </Card>
          ) : null}

          {/* Quick Replies Row */}
          {!isRecording && !pendingAttachment ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.quickRepliesScroll}
              style={styles.quickRepliesContainer}
            >
              {QUICK_REPLIES.map((phrase) => (
                <Pressable
                  key={phrase}
                  style={styles.quickReplyChip}
                  onPress={() => void handleSendText(phrase)}
                  accessibilityRole="button"
                  accessibilityLabel={`ارسال سریع: ${phrase}`}
                >
                  <AppText variant="caption" color="#111B21" style={styles.quickReplyText}>
                    {phrase}
                  </AppText>
                </Pressable>
              ))}
            </ScrollView>
          ) : null}

          {/* Voice Recording Bar */}
          {isRecording ? (
            <View style={styles.recordingBar}>
              <View style={styles.recordingTimerGroup}>
                <View style={styles.recordDot} />
                <AppText variant="label" color="#EA4335">
                  در حال ضبط...
                </AppText>
                <AppText variant="label" color="#111B21">
                  {toPersianDigits(recordingSeconds)} ثانیه
                </AppText>
              </View>

              <View style={styles.recordingButtons}>
                <Pressable
                  onPress={() => void handleCancelRecording()}
                  style={styles.cancelRecBtn}
                  accessibilityRole="button"
                  accessibilityLabel="انصراف از ضبط"
                >
                  <AppText variant="caption" color="#667781">
                    انصراف
                  </AppText>
                </Pressable>
                <Pressable
                  onPress={() => void handleStopVoiceAndSend()}
                  style={styles.sendRecBtn}
                  accessibilityRole="button"
                  accessibilityLabel="ارسال صدا"
                >
                  <AppText variant="label" color="#FFFFFF">
                    ارسال صدا ✓
                  </AppText>
                </Pressable>
              </View>
            </View>
          ) : (
            /* WhatsApp Input Bar: Action button on RIGHT, Attachment on LEFT, Text in MIDDLE */
            <View style={styles.whatsappInputBar}>
              {/* 1. Far RIGHT in RTL: WhatsApp Floating Action Circle Button */}
              {inputText.trim() ? (
                <Pressable
                  onPress={() => void handleSendText()}
                  disabled={isSending}
                  style={styles.actionFloatingButton}
                  accessibilityRole="button"
                  accessibilityLabel="ارسال پیام"
                >
                  <SvgXml xml={SEND_ICON_XML} width={19} height={19} />
                </Pressable>
              ) : (
                <Pressable
                  onPress={() => void handleStartRecording()}
                  style={styles.actionFloatingButton}
                  accessibilityRole="button"
                  accessibilityLabel="ضبط صدا"
                >
                  <SvgXml xml={MIC_ICON_XML} width={22} height={22} />
                </Pressable>
              )}

              {/* 2. Middle & Left in RTL: Rounded White Pill Container */}
              <View style={styles.pillInputContainer}>
                {/* Text input occupying main area, aligned to right */}
                <TextInput
                  value={inputText}
                  onChangeText={setInputText}
                  placeholder={t.typeMessagePlaceholder}
                  placeholderTextColor="#8696A0"
                  style={styles.chatTextInput}
                  multiline
                  maxLength={1000}
                />

                {/* Attachment Clip Button on the LEFT side of pill */}
                <Pressable
                  onPress={() => setShowAttachMenu((prev) => !prev)}
                  style={styles.attachButton}
                  accessibilityRole="button"
                  accessibilityLabel="پیوست فایل"
                >
                  <SvgXml xml={ATTACH_ICON_XML} width={22} height={22} />
                </Pressable>
              </View>
            </View>
          )}

          {/* Quick Attachment Sheet */}
          {showAttachMenu ? (
            <View style={styles.attachPopup}>
              <Pressable
                style={styles.attachPopupItem}
                onPress={() => void handlePickImage()}
                accessibilityRole="button"
              >
                <AppText variant="label" color="#111B21">
                  🖼️ عکس از گالری
                </AppText>
              </Pressable>
              <View style={styles.attachPopupDivider} />
              <Pressable
                style={styles.attachPopupItem}
                onPress={() => void handlePickVideo()}
                accessibilityRole="button"
              >
                <AppText variant="label" color="#111B21">
                  🎥 ویدیو
                </AppText>
              </Pressable>
            </View>
          ) : null}
        </View>
      </KeyboardAvoidingView>

      {/* 4. Full-Screen Media Viewer Modal */}
      {viewerMedia ? (
        <Modal
          visible={true}
          transparent
          animationType="fade"
          onRequestClose={() => setViewerMedia(null)}
        >
          <View style={styles.viewerBackdrop}>
            <View style={styles.viewerHeader}>
              <Pressable
                onPress={() => setViewerMedia(null)}
                style={styles.viewerCloseBtn}
                accessibilityRole="button"
                accessibilityLabel="بستن"
              >
                <AppText variant="title" color="#FFFFFF">
                  ✕
                </AppText>
              </Pressable>
              <AppText variant="label" color="#FFFFFF">
                {viewerMedia.type === "IMAGE" ? "نمایش تصویر" : "پخش ویدیو"}
              </AppText>
            </View>

            <View style={styles.viewerMediaContent}>
              {viewerMedia.type === "IMAGE" ? (
                <Image
                  source={{ uri: viewerMedia.url }}
                  style={styles.viewerImage}
                  resizeMode="contain"
                />
              ) : (
                <Video
                  source={{ uri: viewerMedia.url }}
                  style={styles.viewerVideo}
                  useNativeControls
                  resizeMode={ResizeMode.CONTAIN}
                  isLooping={false}
                  shouldPlay
                />
              )}
            </View>

            {viewerMedia.caption ? (
              <View style={styles.viewerCaptionBox}>
                <AppText variant="body" color="#FFFFFF" align="center">
                  {viewerMedia.caption}
                </AppText>
              </View>
            ) : null}
          </View>
        </Modal>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  // Contact & Chat List styles
  chatListScroll: {
    paddingHorizontal: 16,
    paddingBottom: spacing.xl,
    paddingTop: 8,
  },
  sectionHeaderRow: {
    marginBottom: 8,
    marginTop: 4,
  },
  sectionHeader: {
    fontSize: 12,
    fontWeight: "700",
  },
  chatListItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 12,
    gap: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
    borderWidth: 1,
    borderColor: "#E9EDEF",
  },
  avatarWrapper: {
    position: "relative",
  },
  onlineDot: {
    position: "absolute",
    bottom: 0,
    right: 0,
    width: 13,
    height: 13,
    borderRadius: 6.5,
    backgroundColor: "#00A884",
    borderWidth: 2,
    borderColor: "#FFFFFF",
  },
  chatItemBody: {
    flex: 1,
    gap: 4,
  },
  chatItemTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  chatItemTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111B21",
  },
  chatItemBottomRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  chatSnippet: {
    flex: 1,
    fontSize: 13,
  },
  chatSnippetUnread: {
    fontWeight: "600",
  },
  whatsappUnreadBadge: {
    backgroundColor: "#00A884", // WhatsApp green
    borderRadius: radius.pill,
    paddingHorizontal: 7,
    paddingVertical: 2,
    minWidth: 20,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 6,
  },
  unreadBadgeText: {
    fontSize: 11,
    fontWeight: "700",
  },

  // Secondary contacts
  contactItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 10,
    gap: 10,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: "#F0F2F5",
  },
  contactInfo: {
    flex: 1,
    gap: 2,
  },
  contactHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  contactName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#111B21",
  },
  priorityBadge: {
    backgroundColor: "rgba(0, 168, 132, 0.12)",
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: radius.pill,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#00A884",
  },
  contactPhone: {
    fontSize: 12,
  },
  chevron: {
    fontSize: 18,
    marginRight: 4,
  },

  // Conversation Screen (WhatsApp theme)
  conversationContainer: {
    flex: 1,
    backgroundColor: "#EFEAE2", // WhatsApp chat background wallpaper tone
  },
  whatsappHeader: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingTop: Platform.OS === "ios" ? 50 : (StatusBar.currentHeight || 24) + 12,
    paddingBottom: 10,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: 1,
    borderBottomColor: "#E9EDEF",
    gap: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  backButton: {
    padding: 6,
    justifyContent: "center",
    alignItems: "center",
  },
  backArrow: {
    fontSize: 20,
    fontWeight: "700",
  },
  headerInfoGroup: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  headerAvatarWrapper: {
    position: "relative",
  },
  headerOnlineDot: {
    position: "absolute",
    bottom: 0,
    right: 0,
    width: 11,
    height: 11,
    borderRadius: 5.5,
    backgroundColor: "#00A884",
    borderWidth: 1.5,
    borderColor: "#FFFFFF",
  },
  headerTitles: {
    flex: 1,
    gap: 2,
    alignItems: "flex-start",
  },
  headerName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111B21",
    textAlign: "right",
  },
  headerStatus: {
    fontSize: 12,
    fontWeight: "500",
    textAlign: "right",
  },

  messagesFlexContainer: {
    flex: 1,
  },
  messagesScroll: {
    flex: 1,
  },
  messagesScrollContent: {
    paddingHorizontal: 8,
    paddingVertical: 10,
  },
  errorBanner: {
    paddingVertical: 4,
    backgroundColor: colors.errorSoft,
  },

  // Bottom Composer (WhatsApp Style)
  fixedComposer: {
    backgroundColor: "transparent",
    paddingHorizontal: 8,
    paddingTop: 4,
    paddingBottom: Platform.OS === "ios" ? 28 : 18,
    gap: 6,
  },
  quickRepliesContainer: {
    maxHeight: 34,
  },
  quickRepliesScroll: {
    gap: 6,
    paddingHorizontal: 4,
  },
  quickReplyChip: {
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 1,
    elevation: 1,
  },
  quickReplyText: {
    fontSize: 12,
    fontWeight: "600",
  },

  // WhatsApp Input Bar: Floating Action on RIGHT, Pill on LEFT (in RTL)
  whatsappInputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 6,
    marginBottom: 4,
  },
  pillInputContainer: {
    flex: 1,
    minHeight: 46,
    maxHeight: 120,
    backgroundColor: "#FFFFFF",
    borderRadius: 23,
    paddingHorizontal: 10,
    paddingVertical: 4,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  attachButton: {
    padding: 6,
  },
  attachIcon: {
    fontSize: 18,
  },
  chatTextInput: {
    flex: 1,
    fontSize: 15,
    color: "#111B21",
    textAlign: "right",
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  actionFloatingButton: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: "#00A884", // WhatsApp brand green
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    elevation: 3,
  },
  sendIcon: {
    fontSize: 16,
    marginLeft: 2,
  },
  micIcon: {
    fontSize: 18,
  },

  // Recording Bar
  recordingBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#FFFFFF",
    borderRadius: 23,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#FECACA",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  recordingTimerGroup: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  recordDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#EA4335",
  },
  recordingButtons: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  cancelRecBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  sendRecBtn: {
    backgroundColor: "#00A884",
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: radius.pill,
  },

  // Attachment popup
  attachPopup: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    paddingVertical: 4,
    marginHorizontal: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  attachPopupItem: {
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  attachPopupDivider: {
    height: 1,
    backgroundColor: "#F1F5F9",
  },

  // Preview attachment
  previewCard: {
    padding: spacing.sm,
    gap: spacing.xs,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    backgroundColor: "#FFFFFF",
  },
  previewHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  previewContentRow: {
    flexDirection: "row",
    gap: spacing.sm,
    alignItems: "center",
  },
  previewThumbnail: {
    width: 60,
    height: 60,
    borderRadius: 10,
    backgroundColor: "#E2E8F0",
  },
  videoPreviewFallback: {
    backgroundColor: "#111B21",
    justifyContent: "center",
    alignItems: "center",
  },
  previewDetails: {
    flex: 1,
  },
  captionInput: {
    borderWidth: 1,
    borderColor: "#E2E8F0",
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 13,
    color: "#111B21",
    textAlign: "right",
  },
  previewActions: {
    marginTop: 4,
  },

  // Full-screen viewer
  viewerBackdrop: {
    flex: 1,
    backgroundColor: "rgba(11, 17, 26, 0.96)",
    justifyContent: "space-between",
  },
  viewerHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: Platform.OS === "ios" ? 54 : (StatusBar.currentHeight || 24) + 16,
    paddingHorizontal: 20,
  },
  viewerCloseBtn: {
    padding: 8,
  },
  viewerMediaContent: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  viewerImage: {
    width: "100%",
    height: "100%",
  },
  viewerVideo: {
    width: "100%",
    height: 320,
  },
  viewerCaptionBox: {
    paddingHorizontal: 20,
    paddingBottom: Platform.OS === "ios" ? 40 : 20,
  },
});
