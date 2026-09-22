import { useState } from "react";
import { Share, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatPersianDate, t } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import {
  AppText,
  Avatar,
  Button,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Screen,
  StatusBadge,
  TextField,
  TopAppBar,
} from "../../src/components";
import { listInvitations, listMembers, revokeInvitation, revokeMember, suspendMember } from "../../src/api/endpoints/identity";
import { listContacts, updateContact } from "../../src/api/endpoints/communication";
import { queryKeys } from "../../src/api/queryKeys";
import { useElderStore } from "../../src/stores/elderStore";
import { usePermissions } from "../../src/permissions/usePermission";
import { PERMISSIONS } from "../../src/permissions/codes";
import {
  invitationShareMessage,
  pendingInvitationTitle,
  roleLabel,
} from "../../src/services/family/invitationDisplay";
import type { Invitation } from "../../src/api/types";

export default function FamilyScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();
  const members = useQuery({
    queryKey: elderId ? queryKeys.members(elderId) : ["members"],
    enabled: Boolean(elderId),
    queryFn: () => listMembers(elderId as string),
  });
  const invitations = useQuery({
    queryKey: elderId ? queryKeys.invitations(elderId) : ["invitations"],
    enabled: Boolean(elderId) && can(PERMISSIONS.MANAGE_MEMBERS),
    queryFn: () => listInvitations(elderId as string),
  });
  const contacts = useQuery({
    queryKey: elderId ? queryKeys.contacts(elderId) : ["contacts"],
    enabled: Boolean(elderId) && can(PERMISSIONS.VIEW_ELDER_STATUS),
    queryFn: () => listContacts(elderId as string),
  });

  const revokeInv = useMutation({
    mutationFn: (id: string) => revokeInvitation(elderId as string, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.invitations(elderId as string) }),
  });
  const suspend = useMutation({
    mutationFn: (id: string) => suspendMember(elderId as string, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.members(elderId as string) }),
  });
  const revoke = useMutation({
    mutationFn: (id: string) => revokeMember(elderId as string, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.members(elderId as string) }),
  });

  const [editingContactId, setEditingContactId] = useState<string | null>(null);
  const [editDisplayName, setEditDisplayName] = useState("");

  const updateContactMut = useMutation({
    mutationFn: ({ id, displayName }: { id: string; displayName: string }) =>
      updateContact(id, { display_name: displayName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.contacts(elderId as string) });
      setEditingContactId(null);
    },
  });

  async function shareInvitation(invite: Invitation) {
    await Share.share({
      message: invitationShareMessage(roleLabel(invite.role_code), invite.invite_code),
    });
  }

  if (members.isPending) {
    return (
      <Screen>
        <TopAppBar title={t.familyTitle} showBack />
        <LoadingSkeleton />
      </Screen>
    );
  }
  if (members.isError) {
    return (
      <Screen>
        <TopAppBar title={t.familyTitle} showBack />
        <ErrorState onRetry={() => void members.refetch()} />
      </Screen>
    );
  }

  return (
    <Screen>
      <TopAppBar title={t.familyTitle} showBack />
      <AppText variant="body" color={colors.textSecondary}>
        {t.familySubtitle}
      </AppText>
      <AppText variant="title">{t.careTeam}</AppText>
      {members.data?.map((member) => (
        <Card key={member.id}>
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <AppText variant="label">{member.user_full_name}</AppText>
              <StatusBadge label={roleLabel(member.role_code)} tone={member.is_primary ? "success" : "info"} />
            </View>
            <Avatar name={member.user_full_name} size={64} />
          </View>
          {can(PERMISSIONS.MANAGE_MEMBERS) && !member.is_primary ? (
            <View style={styles.actions}>
              <Button label={t.suspendMember} variant="secondary" onPress={() => suspend.mutate(member.id)} />
              <Button label={t.revokeMember} variant="danger" onPress={() => revoke.mutate(member.id)} />
            </View>
          ) : null}
        </Card>
      ))}
      {can(PERMISSIONS.MANAGE_MEMBERS)
        ? invitations.data
            ?.filter((item) => item.status === "PENDING")
            .map((invite) => (
              <Card key={invite.id}>
                <AppText variant="label">{pendingInvitationTitle()}</AppText>
                <StatusBadge label={roleLabel(invite.role_code)} tone="warning" />
                <AppText variant="caption" color={colors.textSecondary}>
                  {t.expiresAt}: {formatPersianDate(invite.expires_at)}
                </AppText>
                <View style={styles.actions}>
                  <Button label={t.inviteShare} variant="secondary" onPress={() => void shareInvitation(invite)} />
                  <Button label={t.revokeInvite} variant="danger" onPress={() => revokeInv.mutate(invite.id)} />
                </View>
              </Card>
            ))
        : null}
      {can(PERMISSIONS.MANAGE_MEMBERS) ? (
        <Button label={t.inviteMember} icon="user_plus" onPress={() => router.push("/(app)/family/invite")} />
      ) : null}

      <AppText variant="title">{t.trustedContacts}</AppText>
      <AppText variant="caption" color={colors.textSecondary}>
        {t.trustedContactsHint}
      </AppText>
      {contacts.data?.length ? (
        contacts.data.map((contact) => (
          <Card key={contact.id}>
            {editingContactId === contact.id ? (
              <View style={styles.actions}>
                <AppText variant="label">نام نمایشی مخاطب در تبلت سالمند</AppText>
                <TextField
                  label="نام در تبلت (مثلاً: پسر، دختر، علی)"
                  value={editDisplayName}
                  onChangeText={setEditDisplayName}
                />
                <View style={{ flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs }}>
                  <View style={{ flex: 1 }}>
                    <Button
                      label="ذخیره"
                      variant="primary"
                      onPress={() => updateContactMut.mutate({ id: contact.id, displayName: editDisplayName })}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Button
                      label="انصراف"
                      variant="secondary"
                      onPress={() => setEditingContactId(null)}
                    />
                  </View>
                </View>
              </View>
            ) : (
              <>
                <View style={styles.row}>
                  <Avatar name={contact.display_name} size={48} />
                  <View style={{ flex: 1 }}>
                    <AppText variant="label">{contact.display_name}</AppText>
                    <AppText variant="caption" color={colors.textSecondary}>
                      {contact.phone || t.trustedContacts}
                    </AppText>
                  </View>
                </View>
                {can(PERMISSIONS.MANAGE_CONTACTS) || can(PERMISSIONS.MANAGE_MEMBERS) ? (
                  <View style={{ marginTop: spacing.sm }}>
                    <Button
                      label="ویرایش نام در تبلت"
                      variant="secondary"
                      onPress={() => {
                        setEditingContactId(contact.id);
                        setEditDisplayName(contact.display_name);
                      }}
                    />
                  </View>
                ) : null}
              </>
            )}
          </Card>
        ))
      ) : (
        <EmptyState title={t.empty} body={t.trustedContactsHint} />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  actions: { gap: spacing.sm, marginTop: spacing.md },
});
