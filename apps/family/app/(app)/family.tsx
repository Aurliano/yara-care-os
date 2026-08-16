import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { t } from "../../src/i18n";
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
  TopAppBar,
} from "../../src/components";
import { listInvitations, listMembers, revokeInvitation, revokeMember, suspendMember } from "../../src/api/endpoints/identity";
import { listContacts } from "../../src/api/endpoints/communication";
import { queryKeys } from "../../src/api/queryKeys";
import { useElderStore } from "../../src/stores/elderStore";
import { usePermissions } from "../../src/permissions/usePermission";
import { PERMISSIONS } from "../../src/permissions/codes";
import type { RoleCode } from "../../src/api/types";

function roleLabel(code: RoleCode | string): string {
  if (code === "PRIMARY_CAREGIVER") return t.rolePrimary;
  if (code === "CAREGIVER") return t.roleCaregiver;
  if (code === "VIEWER") return t.roleViewer;
  return code;
}

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

  if (members.isPending) {
    return (
      <Screen>
        <LoadingSkeleton />
      </Screen>
    );
  }
  if (members.isError) {
    return (
      <Screen>
        <ErrorState onRetry={() => void members.refetch()} />
      </Screen>
    );
  }

  return (
    <Screen>
      <TopAppBar title={t.familyTitle} showBack showBell={false} />
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
                <AppText variant="label">{invite.invite_code}</AppText>
                <StatusBadge label={t.pendingInvite} tone="warning" />
                <Button label={t.revokeInvite} variant="ghost" onPress={() => revokeInv.mutate(invite.id)} />
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
            <AppText variant="label" align="center">
              {contact.display_name}
            </AppText>
            <AppText variant="caption" color={colors.textSecondary} align="center">
              {contact.preferred_channel}
            </AppText>
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
