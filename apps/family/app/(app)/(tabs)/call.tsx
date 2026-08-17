import { useState } from "react";
import { Linking, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { AppText, Button, Card, EmptyState, ErrorState, LoadingSkeleton, Screen, TopAppBar } from "../../../src/components";
import { PermissionDenied } from "../../../src/components/PermissionDenied";
import { t } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import { listContacts, startCall } from "../../../src/api/endpoints/communication";
import { queryKeys } from "../../../src/api/queryKeys";
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { ApiError } from "../../../src/api/errors";
import type { Contact } from "../../../src/api/types";

export default function CallScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can, isPending } = usePermissions();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const contacts = useQuery({
    queryKey: elderId ? queryKeys.contacts(elderId) : ["contacts"],
    enabled: Boolean(elderId) && can(PERMISSIONS.INITIATE_CALL),
    queryFn: () => listContacts(elderId as string),
  });

  if (!isPending && !can(PERMISSIONS.INITIATE_CALL)) {
    return <PermissionDenied />;
  }

  async function onCall(contact: Contact) {
    if (!elderId) return;
    setBusyId(contact.id);
    setError(null);
    try {
      const result = await startCall({
        elder_id: elderId,
        channel: "VOICE",
        recipient_contact_id: contact.id,
      });
      await Linking.openURL(result.joinToken);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError(t.callBusy);
      } else if (err instanceof ApiError && err.status === 403) {
        setError(t.callPermissionBody);
      } else {
        setError(t.callFailed);
      }
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

  const items = contacts.data ?? [];

  return (
    <Screen>
      <TopAppBar title={t.callTitle} />
      <AppText variant="body" color={colors.textSecondary}>
        {t.callSubtitle}
      </AppText>
      {error ? (
        <AppText variant="caption" color={colors.error}>
          {error}
        </AppText>
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
              <Button
                label={t.startVoiceCall}
                icon="phone"
                loading={busyId === contact.id}
                onPress={() => void onCall(contact)}
              />
            </View>
          </Card>
        ))
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.md },
});
