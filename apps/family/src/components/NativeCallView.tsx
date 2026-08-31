import "../polyfills";
import { useEffect, useState } from "react";
import { Modal, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LiveKitRoom, useTracks, VideoTrack, useConnectionState, useLocalParticipant } from "@livekit/react-native";
import { Track, ConnectionState } from "livekit-client";
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

function CallContent({
  session,
  titleName,
  onHangup,
}: any) {
  const connectionState = useConnectionState();
  const isVideo = session?.channel === "VIDEO";
  const isConnected = connectionState === ConnectionState.Connected;
  
  const tracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: false }]);
  const remoteVideoTracks = tracks.filter((t) => t.participant.isLocal === false);
  const localVideoTracks = tracks.filter((t) => t.participant.isLocal === true);
  
  const { localParticipant } = useLocalParticipant();
  const isMuted = !localParticipant?.isMicrophoneEnabled;
  const isCameraOn = localParticipant?.isCameraEnabled;

  const [callDuration, setCallDuration] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isConnected) {
      interval = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isConnected]);

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
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
          {isConnected ? `${t.callConnected} - ${formatDuration(callDuration)}` : t.callConnecting}
        </AppText>
      </View>

      {/* Center Media Area */}
      <View style={styles.mediaContainer}>
        {(!isVideo || !isConnected) && (
          <View style={styles.avatarWrapper}>
            <Avatar name={titleName} size={sizes.avatarLg * 2} />
          </View>
        )}
        {isVideo && isConnected && remoteVideoTracks.length > 0 && (
           <VideoTrack trackRef={remoteVideoTracks[0]} style={styles.remoteVideo} />
        )}
        {isVideo && isConnected && localVideoTracks.length > 0 && (
           <View style={styles.localVideoContainer}>
             <VideoTrack trackRef={localVideoTracks[0]} style={styles.localVideo} />
           </View>
        )}
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <View style={styles.controlRow}>
          <Button
            label={isMuted ? t.callUnmute : t.callMute}
            variant={isMuted ? "secondary" : "ghost"}
            style={styles.actionBtn}
            onPress={() => localParticipant?.setMicrophoneEnabled(!!isMuted)}
          />
          {isVideo ? (
            <Button
              label={isCameraOn ? t.callCameraOff : t.callCameraOn}
              variant={isCameraOn ? "ghost" : "secondary"}
              style={styles.actionBtn}
              onPress={() => localParticipant?.setCameraEnabled(!isCameraOn)}
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
  );
}

export function NativeCallView({
  visible,
  session,
  contactName,
  onHangup,
}: Props) {
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [hasPermissions, setHasPermissions] = useState(false);

  const titleName = contactName || t.navCall;

  useEffect(() => {
    if (!visible || !session) {
      setHasPermissions(false);
      return;
    }

    let isMounted = true;
    async function initPerms() {
      const perms = await requestMediaPermissions(session!.channel === "VIDEO" ? "VIDEO" : "VOICE");
      if (!perms.microphone || (session!.channel === "VIDEO" && !perms.camera)) {
        if (isMounted) setPermissionError(t.mediaPermissionRequired);
      } else {
        if (isMounted) {
            setPermissionError(null);
            setHasPermissions(true);
        }
      }
    }
    void initPerms();
    return () => { isMounted = false; };
  }, [visible, session?.channel]);

  if (!visible || !session) return null;

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
      {!hasPermissions ? (
        <SafeAreaView style={[styles.container, { justifyContent: 'center' }]}>
           <AppText align="center" color={colors.error}>{permissionError || "Requesting permissions..."}</AppText>
           <Button label={t.hangUp} onPress={onHangup} style={{ marginTop: 20 }} />
        </SafeAreaView>
      ) : (
        <LiveKitRoom
          serverUrl={LIVEKIT_URL}
          token={session.joinToken}
          connect={true}
          audio={true}
          video={session.channel === "VIDEO"}
          onDisconnected={onHangup}
        >
           <CallContent session={session} titleName={titleName} onHangup={onHangup} />
        </LiveKitRoom>
      )}
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
    zIndex: 10,
  },
  mediaContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    position: 'relative'
  },
  remoteVideo: {
    width: "100%",
    height: "100%",
    backgroundColor: "transparent",
    position: "absolute",
    top: 0,
    left: 0,
  },
  localVideoContainer: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    width: 120,
    height: 160,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'white',
    overflow: 'hidden',
    zIndex: 20
  },
  localVideo: {
    flex: 1,
    backgroundColor: "transparent",
  },
  avatarWrapper: {
    padding: spacing.xl,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceSoft,
    position: 'absolute',
    zIndex: 1
  },
  controls: {
    gap: spacing.md,
    paddingBottom: spacing.md,
    zIndex: 10
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
