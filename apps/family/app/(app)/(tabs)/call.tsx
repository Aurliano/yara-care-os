import { useEffect, useMemo, useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import {
  AppText,
  Button,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  NativeCallView,
  Screen,
  TopAppBar,
} from "../../../src/components";
import { PermissionDenied } from "../../../src/components/PermissionDenied";
import { t } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import { acceptSession, listContacts, listSessions } from "../../../src/api/endpoints/communication";
import { queryKeys } from "../../../src/api/queryKeys";
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { requestMediaPermissions } from "../../../src/permissions/mediaPermissions";
import { mapCallFailureMessage } from "../../../src/communication/CommunicationGateway";
import { voiceMessageAvailability } from "../../../src/services/communication/voiceMessageRepository";
import type { Contact } from "../../../src/api/types";
import {
  createFamilyCommunicationRuntime,
  INCOMING_SESSION_STATUSES,
  isActiveCallState,
} from "../../../src/communication";
import type { CallSession } from "../../../src/communication";

export default function CallScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can, isPending } = usePermissions();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<CallSession | null>(null);
  const runtime = useMemo(
    () => createFamilyCommunicationRuntime({ onSession: setSession }),
    [],
  );
  const voiceMessage = voiceMessageAvailability();
  const contacts = useQuery({
    queryKey: elderId ? queryKeys.contacts(elderId) : ["contacts"],
    enabled: Boolean(elderId) && can(PERMISSIONS.INITIATE_CALL),
    queryFn: () => listContacts(elderId as string),
  });
  const remoteSessions = useQuery({
    queryKey: elderId ? queryKeys.sessions(elderId) : ["sessions"],
    enabled: Boolean(elderId) && can(PERMISSIONS.INITIATE_CALL),
    queryFn: () => listSessions(elderId as string),
    refetchInterval: 4000,
  });

  useEffect(() => {
    void runtime.recover();
  }, [runtime]);

  if (!isPending && !can(PERMISSIONS.INITIATE_CALL)) {
    return <PermissionDenied />;
  }

  const localActive = session && isActiveCallState(session.runtimeState);
  const incoming = (remoteSessions.data ?? []).find(
    (item) =>
      (INCOMING_SESSION_STATUSES as readonly string[]).includes(item.status) &&
      item.channel !== "MESSAGE" &&
      (!localActive || session?.sessionId !== item.id),
  );
  const showIncoming = Boolean(incoming) && !localActive;

  const items = contacts.data ?? [];
  const activeContact = items.find((c) => c.id === session?.recipientContactId);
  const activeContactName = activeContact?.display_name || t.navCall;

  async function joinMedia(next: CallSession) {
    if (next.sessionId) {
      try {
        await acceptSession(next.sessionId);
      } catch {
        // Accept is best-effort; in-app media proceeds.
      }
    }
  }

  async function onCall(contact: Contact, channel: "VOICE" | "VIDEO") {
    if (!elderId) return;
    setBusyId(`${contact.id}:${channel}`);
    setError(null);
    try {
      const perms = await requestMediaPermissions(channel);
      if (!perms.microphone || (channel === "VIDEO" && !perms.camera)) {
        setError(t.mediaPermissionRequired);
        return;
      }
      const result = await runtime.startCall(elderId, channel, contact.id);
      if (!result.ok) {
        setError(mapCallFailureMessage(result.error));
        return;
      }
      await joinMedia(result.data);
    } catch (error) {
      setError(mapCallFailureMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function onAnswerIncoming() {
    if (!elderId || !incoming) return;
    setBusyId("incoming");
    setError(null);
    try {
      const channel = incoming.channel === "VIDEO" ? "VIDEO" : "VOICE";
      const perms = await requestMediaPermissions(channel);
      if (!perms.microphone || (channel === "VIDEO" && !perms.camera)) {
        setError(t.mediaPermissionRequired);
        return;
      }
      const result = await runtime.joinIncomingCall(elderId, channel);
      if (!result.ok) {
        throw result.error;
      }
      await joinMedia(result.data);
    } catch (error) {
      setError(mapCallFailureMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function onHangup() {
    setBusyId("hangup");
    try {
      await runtime.endCall();
    } finally {
      setBusyId(null);
    }
  }

  if (contacts.isPending) {
    return (
      <Screen>
        <TopAppBar title={t.callTitle} />
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (contacts.isError) {
    return (
      <Screen>
        <TopAppBar title={t.callTitle} />
        <ErrorState onRetry={() => void contacts.refetch()} />
      </Screen>
    );
  }

  return (
    <Screen>
      <TopAppBar title={t.callTitle} />
      <AppText variant="body" color={colors.textSecondary}>
        {t.callSubtitle}
      </AppText>
      {voiceMessage.available ? null : (
        <AppText variant="caption" color={colors.textSecondary}>
          {t.voiceMessageUnavailable}
        </AppText>
      )}
      {error ? (
        <AppText variant="caption" color={colors.error}>
          {error}
        </AppText>
      ) : null}
      {showIncoming && incoming ? (
        <Card accent="success">
          <AppText variant="label">{t.incomingCallTitle}</AppText>
          <AppText variant="caption" color={colors.textSecondary}>
            {t.incomingCallBody}
          </AppText>
          <Button
            label={t.answerCall}
            icon="phone"
            loading={busyId === "incoming"}
            onPress={() => void onAnswerIncoming()}
          />
        </Card>
      ) : null}
      {localActive ? (
        <Card>
          <AppText variant="label">{session.channel === "VIDEO" ? t.startVideoCall : t.startVoiceCall}</AppText>
          <Button label={t.hangUp} loading={busyId === "hangup"} onPress={() => void onHangup()} />
        </Card>
      ) : null}
      {items.length === 0 ? (
        <EmptyState
          title={t.callNoContactsTitle}
          body={t.callNoContactsBody}
          actionLabel={t.goToFamily}
          onAction={() => router.push("/(app)/family")}
        />
      ) : (
        items.map((contact) => (
          <Card key={contact.id}>
            <View style={styles.row}>
              <View style={{ flex: 1 }}>
                <AppText variant="label">{contact.display_name}</AppText>
                <AppText variant="caption" color={colors.textSecondary}>
                  {contact.phone || t.navCall}
                </AppText>
              </View>
              <View style={styles.actions}>
                <Button
                  label={t.startVideoCall}
                  icon="phone"
                  loading={busyId === `${contact.id}:VIDEO`}
                  onPress={() => void onCall(contact, "VIDEO")}
                />
                <Button
                  label={t.sendVoiceMessage}
                  variant="secondary"
                  disabled={!voiceMessage.available}
                  onPress={() => undefined}
                />
              </View>
            </View>
          </Card>
        ))
      )}

      {/* In-app Native Call View for LiveKit */}
      {Boolean(localActive) ? (
        <NativeCallView
          visible={Boolean(localActive)}
          session={session}
          contactName={activeContactName}
          onHangup={() => void onHangup()}
        />
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.md },
  actions: { gap: spacing.sm },
});
