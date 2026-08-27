import "../polyfills";
import { useEffect, useRef, useState } from "react";
import { Modal, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Room, RoomEvent } from "livekit-client";
import { colors, radius, sizes, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { Avatar } from "./Avatar";
import { Button } from "./Button";
import { t } from "../i18n";
import { requestMediaPermissions } from "../permissions/mediaPermissions";
import type { CallSession } from "../communication";

type Props = {
  visible: boolean;
  session: CallSession | null;
  contactName?: string;
  onHangup: () => void;
  onMuteToggle?: (muted: boolean) => void;
  onCameraToggle?: (cameraOn: boolean) => void;
};

const LIVEKIT_URL = "wss://yara-care-8qxaz9wd.livekit.cloud";

/**
 * Pure Native Elder-friendly Call overlay for the Family App.
 * Manages LiveKit SFU signaling, call status, and responsive media controls with zero native crashes.
 */
export function NativeCallView({
  visible,
  session,
  contactName,
  onHangup,
  onMuteToggle,
  onCameraToggle,
}: Props) {
  const [isMuted, setIsMuted] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(session?.channel === "VIDEO");
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [roomConnected, setRoomConnected] = useState(false);
  const roomRef = useRef<Room | null>(null);

  const isVideo = session?.channel === "VIDEO";
  const isConnected = roomConnected || session?.runtimeState === "Connected";
  const titleName = contactName || t.navCall;

  useEffect(() => {
    if (!visible || !session?.joinToken) {
      if (roomRef.current) {
        try {
          roomRef.current.disconnect();
        } catch {
          // Ignored
        }
        roomRef.current = null;
      }
      setRoomConnected(false);
      return;
    }

    let isMounted = true;
    const currentSession = session;

    async function initCall() {
      try {
        const perms = await requestMediaPermissions(currentSession.channel === "VIDEO" ? "VIDEO" : "VOICE");
        if (!perms.microphone || (currentSession.channel === "VIDEO" && !perms.camera)) {
          if (isMounted) setPermissionError(t.mediaPermissionRequired);
        } else {
          if (isMounted) setPermissionError(null);
        }

        if (typeof globalThis !== "undefined" && (globalThis as any).RTCPeerConnection) {
          const room = new Room({
            adaptiveStream: true,
            dynacast: true,
          });
          roomRef.current = room;

          room.on(RoomEvent.Connected, () => {
            if (isMounted) setRoomConnected(true);
          });
          room.on(RoomEvent.Disconnected, () => {
            if (isMounted) setRoomConnected(false);
          });

          await room.connect(LIVEKIT_URL, currentSession.joinToken);
          try {
            await room.localParticipant.setMicrophoneEnabled(true);
          } catch {
            // Ignored
          }
          if (currentSession.channel === "VIDEO") {
            try {
              await room.localParticipant.setCameraEnabled(true);
            } catch {
              // Ignored
            }
          }
        }
      } catch (err) {
        console.warn("[LiveKit Call Notice]:", err);
      }
    }

    void initCall();

    return () => {
      isMounted = false;
      if (roomRef.current) {
        try {
          roomRef.current.disconnect();
        } catch {
          // Ignored
        }
        roomRef.current = null;
      }
    };
  }, [visible, session?.joinToken, session?.channel]);

  if (!visible || !session) return null;

  function toggleMute() {
    const next = !isMuted;
    setIsMuted(next);
    try {
      void roomRef.current?.localParticipant?.setMicrophoneEnabled(!next);
    } catch {
      // Ignored
    }
    onMuteToggle?.(next);
  }

  function toggleCamera() {
    const next = !isCameraOn;
    setIsCameraOn(next);
    try {
      void roomRef.current?.localParticipant?.setCameraEnabled(next);
    } catch {
      // Ignored
    }
    onCameraToggle?.(next);
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <AppText variant="title" color={colors.text} align="center">
            {titleName}
          </AppText>
          <AppText
            variant="caption"
            color={isConnected ? colors.success : colors.textSecondary}
            align="center"
          >
            {isConnected ? t.callConnected : t.callConnecting}
          </AppText>
          {permissionError ? (
            <AppText variant="caption" color={colors.error} align="center" style={styles.errorText}>
              {permissionError}
            </AppText>
          ) : null}
        </View>

        {/* Center Media Area */}
        <View style={styles.mediaContainer}>
          <View style={styles.avatarWrapper}>
            <Avatar name={titleName} size={sizes.avatarLg * 2} />
          </View>
          <AppText variant="body" color={colors.textSecondary} style={styles.sessionStatus}>
            {isVideo ? t.startVideoCall : t.startVoiceCall}
          </AppText>
        </View>

        {/* Controls */}
        <View style={styles.controls}>
          <View style={styles.controlRow}>
            <Button
              label={isMuted ? t.callUnmute : t.callMute}
              variant={isMuted ? "secondary" : "ghost"}
              style={styles.actionBtn}
              onPress={toggleMute}
            />
            {isVideo ? (
              <Button
                label={isCameraOn ? t.callCameraOff : t.callCameraOn}
                variant={isCameraOn ? "ghost" : "secondary"}
                style={styles.actionBtn}
                onPress={toggleCamera}
              />
            ) : null}
          </View>

          <Button
            label={t.hangUp}
            variant="danger"
            style={styles.hangupBtn}
            onPress={onHangup}
          />
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: "space-between",
    paddingHorizontal: spacing.screen,
    paddingVertical: spacing.lg,
  },
  header: {
    alignItems: "center",
    gap: spacing.xs,
    paddingTop: spacing.md,
  },
  errorText: {
    marginTop: spacing.xs,
    paddingHorizontal: spacing.md,
  },
  mediaContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.md,
  },
  avatarWrapper: {
    padding: spacing.xl,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceSoft,
  },
  sessionStatus: {
    marginTop: spacing.sm,
  },
  controls: {
    gap: spacing.md,
    paddingBottom: spacing.md,
  },
  controlRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: spacing.md,
  },
  actionBtn: {
    minWidth: 120,
  },
  hangupBtn: {
    backgroundColor: colors.error,
    borderColor: colors.error,
    borderWidth: 1,
    minHeight: 52,
  },
});
