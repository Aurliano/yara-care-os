import { useEffect, useState } from "react";
import { Alert, Share, StyleSheet, View } from "react-native";
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
import { createContact, listContacts, updateContact } from "../../src/api/endpoints/communication";
import { getMediaDownloadUrl, uploadMedia } from "../../src/api/endpoints/messaging";
import { queryKeys } from "../../src/api/queryKeys";
import { useElderStore } from "../../src/stores/elderStore";
import { getTokenStore } from "../../src/api/tokenStore";
import { usePermissions } from "../../src/permissions/usePermission";
import { PERMISSIONS } from "../../src/permissions/codes";
import {
  invitationShareMessage,
  pendingInvitationTitle,
  roleLabel,
} from "../../src/services/family/invitationDisplay";
import type { Invitation } from "../../src/api/types";

async function getMediaPicker() {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const picker = require("expo-image-picker");
    return picker as typeof import("expo-image-picker");
  } catch {
    return null;
  }
}

export default function FamilyScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [authToken, setAuthToken] = useState<string | null>(null);

  useEffect(() => {
    void getTokenStore().getAccessToken().then(setAuthToken);
  }, []);
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
  const [editPhotoUri, setEditPhotoUri] = useState<string | null>(null);
  const [editPhotoReference, setEditPhotoReference] = useState<string | null>(null);
  const [isPhotoChanged, setIsPhotoChanged] = useState(false);
  const [isSavingContact, setIsSavingContact] = useState(false);

  const [isAddingContact, setIsAddingContact] = useState(false);
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newPhotoUri, setNewPhotoUri] = useState<string | null>(null);
  const [isSubmittingNewContact, setIsSubmittingNewContact] = useState(false);
  const [isSyncingCaregivers, setIsSyncingCaregivers] = useState(false);

  async function handlePickNewPhoto() {
    try {
      const picker = await getMediaPicker();
      if (!picker) {
        Alert.alert("خطا", t.photoPickerError);
        return;
      }
      const perm = await picker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("دسترسی لازم است", t.mediaGalleryPermissionRequired);
        return;
      }
      const result = await picker.launchImageLibraryAsync({
        mediaTypes: picker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
        legacy: true,
      });
      if (!result.canceled && result.assets && result.assets[0]?.uri) {
        setNewPhotoUri(result.assets[0].uri);
      }
    } catch (_e) {
      Alert.alert("خطا", t.photoPickerError);
    }
  }

  async function handleCreateNewContact() {
    if (!elderId) return;
    const trimmedName = newDisplayName.trim();
    if (!trimmedName) {
      Alert.alert("خطا", "لطفاً نام مخاطب را وارد کنید.");
      return;
    }
    try {
      setIsSubmittingNewContact(true);
      let photoRef: string | null = null;
      if (newPhotoUri && (newPhotoUri.startsWith("file:") || newPhotoUri.startsWith("content:"))) {
        const filename = newPhotoUri.split("/").pop() || "contact_photo.jpg";
        const ext = filename.split(".").pop()?.toLowerCase() || "jpg";
        const mimeType = ext === "png" ? "image/png" : ext === "webp" ? "image/webp" : "image/jpeg";
        const formData = new FormData();
        formData.append("file", {
          uri: newPhotoUri,
          name: filename,
          type: mimeType,
        } as any);
        formData.append("media_type", "IMAGE");
        const uploaded = await uploadMedia(formData);
        photoRef = uploaded.id;
      }
      await createContact(elderId, {
        display_name: trimmedName,
        phone: newPhone.trim() || undefined,
        preferred_channel: "VOICE",
        photo_reference: photoRef,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.contacts(elderId) });
      setIsAddingContact(false);
      setNewDisplayName("");
      setNewPhone("");
      setNewPhotoUri(null);
      Alert.alert("موفقیت", "مخاطب جدید به تبلت اضافه شد و به زودی همگام خواهد شد.");
    } catch (err: any) {
      Alert.alert("خطا در ایجاد مخاطب", err?.message || "امکان افزودن مخاطب وجود ندارد.");
    } finally {
      setIsSubmittingNewContact(false);
    }
  }

  async function handleSyncCaregiversToContacts() {
    if (!elderId) return;
    const existingNames = new Set((contacts.data || []).map((c) => c.display_name.trim()));
    const activeMembers = (members.data || []).filter((m) => m.status === "ACTIVE");
    const toAdd = activeMembers.filter((m) => !existingNames.has(m.user_full_name.trim()));

    if (toAdd.length === 0) {
      Alert.alert("اطلاع", "همه مراقبان در حال حاضر به عنوان مخاطب در تبلت ثبت هستند.");
      return;
    }

    try {
      setIsSyncingCaregivers(true);
      for (const m of toAdd) {
        await createContact(elderId, {
          display_name: m.user_full_name.trim(),
          preferred_channel: "VOICE",
        });
      }
      await queryClient.invalidateQueries({ queryKey: queryKeys.contacts(elderId) });
      Alert.alert("موفقیت", `${toAdd.length} مراقب به لیست مخاطبان تبلت افزوده شدند.`);
    } catch (err: any) {
      Alert.alert("خطا", err?.message || "همگام‌سازی مراقبان با تبلت انجام نشد.");
    } finally {
      setIsSyncingCaregivers(false);
    }
  }

  async function handlePickContactPhoto() {
    try {
      const picker = await getMediaPicker();
      if (!picker) {
        Alert.alert("خطا", t.photoPickerError);
        return;
      }
      const perm = await picker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("دسترسی لازم است", t.mediaGalleryPermissionRequired);
        return;
      }
      const result = await picker.launchImageLibraryAsync({
        mediaTypes: picker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
        legacy: true,
      });
      if (!result.canceled && result.assets && result.assets[0]?.uri) {
        setEditPhotoUri(result.assets[0].uri);
        setIsPhotoChanged(true);
      }
    } catch (_e) {
      Alert.alert("خطا", t.photoPickerError);
    }
  }

  function handleRemoveContactPhoto() {
    setEditPhotoUri(null);
    setEditPhotoReference(null);
    setIsPhotoChanged(true);
  }

  async function handleSaveContact(contactId: string) {
    try {
      setIsSavingContact(true);
      let finalPhotoRef: string | null = editPhotoReference;
      if (isPhotoChanged) {
        if (editPhotoUri && (editPhotoUri.startsWith("file:") || editPhotoUri.startsWith("content:"))) {
          const filename = editPhotoUri.split("/").pop() || "contact_photo.jpg";
          const ext = filename.split(".").pop()?.toLowerCase() || "jpg";
          const mimeType = ext === "png" ? "image/png" : ext === "webp" ? "image/webp" : "image/jpeg";
          const formData = new FormData();
          formData.append("file", {
            uri: editPhotoUri,
            name: filename,
            type: mimeType,
          } as any);
          formData.append("media_type", "IMAGE");
          const uploaded = await uploadMedia(formData);
          finalPhotoRef = uploaded.id;
        } else if (!editPhotoUri) {
          finalPhotoRef = null;
        }
      }

      await updateContact(contactId, {
        display_name: editDisplayName,
        photo_reference: finalPhotoRef,
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.contacts(elderId as string) });
      setEditingContactId(null);
      setIsPhotoChanged(false);
    } catch (err: any) {
      Alert.alert("خطا در ذخیره", err?.message || "امکان ذخیره اطلاعات مخاطب وجود ندارد.");
    } finally {
      setIsSavingContact(false);
    }
  }

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
            <Avatar name={member.user_full_name} size={64} />
            <View style={{ flex: 1 }}>
              <AppText variant="label">{member.user_full_name}</AppText>
              <StatusBadge label={roleLabel(member.role_code)} tone={member.is_primary ? "success" : "info"} />
            </View>
          </View>
          {can(PERMISSIONS.MANAGE_MEMBERS) && !member.is_primary ? (
            <View style={styles.actions}>
              {member.status === "ACTIVE" ? (
                <Button label={t.suspendMember} variant="secondary" onPress={() => suspend.mutate(member.id)} />
              ) : null}
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

      {can(PERMISSIONS.MANAGE_CONTACTS) || can(PERMISSIONS.MANAGE_MEMBERS) ? (
        <View style={{ gap: spacing.sm, marginVertical: spacing.sm }}>
          <View style={{ flexDirection: "row", gap: spacing.sm }}>
            <View style={{ flex: 1 }}>
              <Button
                label={isAddingContact ? "بستن فرم" : "+ افزودن مخاطب به تبلت"}
                variant={isAddingContact ? "secondary" : "primary"}
                onPress={() => setIsAddingContact(!isAddingContact)}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Button
                label={isSyncingCaregivers ? "در حال افزودن..." : "افزودن مراقبان به تبلت"}
                variant="secondary"
                disabled={isSyncingCaregivers}
                onPress={() => void handleSyncCaregiversToContacts()}
              />
            </View>
          </View>

          {isAddingContact ? (
            <Card style={styles.addContactCard}>
              <AppText variant="label" color={colors.primary}>
                مشخصات مخاطب جدید در تبلت
              </AppText>
              <View style={styles.editPhotoSection}>
                <Avatar
                  name={newDisplayName || "مخاطب جدید"}
                  photoUrl={newPhotoUri}
                  size={64}
                />
                <View style={{ flex: 1 }}>
                  <Button
                    label={newPhotoUri ? t.changePhoto : t.selectPhoto}
                    variant="secondary"
                    onPress={() => void handlePickNewPhoto()}
                  />
                  {newPhotoUri ? (
                    <View style={{ marginTop: spacing.xs }}>
                      <Button
                        label={t.removePhoto}
                        variant="secondary"
                        onPress={() => setNewPhotoUri(null)}
                      />
                    </View>
                  ) : null}
                </View>
              </View>

              <TextField
                label="نام نمایشی در تبلت (مثلاً: پسرم محمد، دخترم زهرا)"
                value={newDisplayName}
                onChangeText={setNewDisplayName}
              />
              <TextField
                label="شماره تماس (اختیاری)"
                value={newPhone}
                onChangeText={setNewPhone}
                keyboardType="phone-pad"
              />

              <View style={{ flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm }}>
                <View style={{ flex: 1 }}>
                  <Button
                    label={isSubmittingNewContact ? t.saving : "ثبت مخاطب"}
                    variant="primary"
                    disabled={isSubmittingNewContact}
                    onPress={() => void handleCreateNewContact()}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Button
                    label="انصراف"
                    variant="secondary"
                    disabled={isSubmittingNewContact}
                    onPress={() => setIsAddingContact(false)}
                  />
                </View>
              </View>
            </Card>
          ) : null}
        </View>
      ) : null}
      {contacts.data?.length ? (
        contacts.data.map((contact) => (
          <Card key={contact.id}>
            {editingContactId === contact.id ? (
              <View style={styles.actions}>
                <AppText variant="label">{t.editContactTitle}</AppText>

                <View style={styles.editPhotoSection}>
                  <Avatar
                    name={editDisplayName || contact.display_name}
                    photoUrl={editPhotoUri}
                    size={72}
                  />
                  <View style={{ flex: 1, gap: spacing.xs }}>
                    <Button
                      label={editPhotoUri ? t.changePhoto : t.selectPhoto}
                      variant="secondary"
                      onPress={() => void handlePickContactPhoto()}
                    />
                    {editPhotoUri ? (
                      <Button
                        label={t.removePhoto}
                        variant="secondary"
                        onPress={handleRemoveContactPhoto}
                      />
                    ) : null}
                  </View>
                </View>

                <TextField
                  label="نام در تبلت (مثلاً: پسر، دختر، علی)"
                  value={editDisplayName}
                  onChangeText={setEditDisplayName}
                />
                <View style={{ flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs }}>
                  <View style={{ flex: 1 }}>
                    <Button
                      label={isSavingContact ? t.saving : "ذخیره"}
                      variant="primary"
                      disabled={isSavingContact}
                      onPress={() => void handleSaveContact(contact.id)}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Button
                      label="انصراف"
                      variant="secondary"
                      disabled={isSavingContact}
                      onPress={() => setEditingContactId(null)}
                    />
                  </View>
                </View>
              </View>
            ) : (
              <>
                <View style={styles.row}>
                  <Avatar
                    name={contact.display_name}
                    photoUrl={contact.photo_reference ? getMediaDownloadUrl(contact.photo_reference, authToken) : null}
                    size={48}
                  />
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
                      label="ویرایش مخاطب در تبلت"
                      variant="secondary"
                      onPress={() => {
                        setEditingContactId(contact.id);
                        setEditDisplayName(contact.display_name);
                        setEditPhotoReference(contact.photo_reference);
                        setEditPhotoUri(
                          contact.photo_reference
                            ? getMediaDownloadUrl(contact.photo_reference, authToken)
                            : null
                        );
                        setIsPhotoChanged(false);
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
  editPhotoSection: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.sm,
  },
  addContactCard: {
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    gap: spacing.sm,
  },
});
