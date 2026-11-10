import { useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Modal, StyleSheet, View } from "react-native";
import {
  endCareActivity,
  getCareActivity,
  listCompletions,
  listPrescriptions,
  pauseCareActivity,
  resumeCareActivity,
  updateCareActivity,
  updatePrescription,
} from "../../../src/api/endpoints/care";
import { listOccurrences, skipOccurrence } from "../../../src/api/endpoints/scheduling";
import { ApiError } from "../../../src/api/errors";
import {
  AppText,
  Button,
  Card,
  ErrorState,
  LoadingSkeleton,
  Screen,
  TextField,
  TopAppBar,
} from "../../../src/components";
import {
  t,
  formatClock,
  formatRelative,
  careActivityStatusLabel,
  completionStateLabel,
  occurrenceStatusLabel,
} from "../../../src/i18n";
import { firstParam } from "../../../src/navigation/params";
import { colors, radius, spacing } from "../../../src/theme/tokens";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { visualKindFor } from "../../../src/services/program/activityKind";
import { invalidateProgramQueries } from "../../../src/services/program/todayProgram";
import { useElderStore } from "../../../src/stores/elderStore";
import { endOfLocalDay, startOfLocalDay } from "../../../src/i18n/dates";
import type { Occurrence, Prescription } from "../../../src/api/types";

export default function ActivityDetailScreen() {
  const activityId = firstParam(useLocalSearchParams<{ activityId: string }>().activityId) ?? "";
  const router = useRouter();
  const queryClient = useQueryClient();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();

  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editSubtitle, setEditSubtitle] = useState("");
  const [editInstructions, setEditInstructions] = useState("");
  const [showEndConfirm, setShowEndConfirm] = useState(false);

  const refreshProgram = () => invalidateProgramQueries(queryClient, elderId, activityId);

  const query = useQuery({
    queryKey: ["care-activity", activityId],
    enabled: Boolean(activityId),
    queryFn: () => getCareActivity(activityId),
  });

  const prescriptionsQuery = useQuery({
    queryKey: elderId ? ["elder", elderId, "prescriptions"] : ["prescriptions"],
    enabled: Boolean(elderId),
    queryFn: () => listPrescriptions(elderId as string),
  });

  const completions = useQuery({
    queryKey: ["care-activity", activityId, "completions"],
    enabled: Boolean(activityId),
    queryFn: () => listCompletions(activityId),
  });

  const occurrences = useQuery({
    queryKey: ["care-activity", activityId, "occurrences"],
    enabled: Boolean(query.data?.schedule_definition_id),
    queryFn: async () => {
      const result = await listOccurrences(query.data!.schedule_definition_id, {
        type: "between",
        start: startOfLocalDay().toISOString(),
        end: endOfLocalDay().toISOString(),
      });
      return (Array.isArray(result) ? result : [result]) as Occurrence[];
    },
  });

  const prescription = (prescriptionsQuery.data ?? []).find(
    (p: Prescription) => p.care_activity_id === activityId,
  );

  const pause = useMutation({
    mutationFn: () => pauseCareActivity(activityId),
    onSuccess: refreshProgram,
  });

  const resume = useMutation({
    mutationFn: () => resumeCareActivity(activityId),
    onSuccess: refreshProgram,
  });

  const end = useMutation({
    mutationFn: () => endCareActivity(activityId),
    onSuccess: () => {
      setShowEndConfirm(false);
      refreshProgram();
    },
  });

  const skip = useMutation({
    mutationFn: (occurrenceId: string) => skipOccurrence(occurrenceId),
    onSuccess: refreshProgram,
  });

  const update = useMutation({
    mutationFn: async () => {
      await updateCareActivity(activityId, {
        display_title: editTitle.trim(),
        display_subtitle: editSubtitle.trim(),
      });
      if (prescription) {
        await updatePrescription(prescription.care_activity_id, {
          display_title: editTitle.trim(),
          display_subtitle: editSubtitle.trim(),
          dosage_information: editSubtitle.trim(),
          elder_friendly_description: editInstructions.trim(),
        });
      }
    },
    onSuccess: () => {
      setIsEditing(false);
      refreshProgram();
    },
  });

  if (query.isPending) {
    return (
      <Screen>
        <LoadingSkeleton />
      </Screen>
    );
  }
  if (query.isError || !query.data) {
    return (
      <Screen>
        <ErrorState onRetry={() => void query.refetch()} />
      </Screen>
    );
  }

  const activity = query.data;
  const isMedication = activity.activity_type === "MEDICATION";
  const canMutateMedication = isMedication && can(PERMISSIONS.MANAGE_MEDICATION);
  const kind = visualKindFor(activity.activity_type, activity.display_title);
  const next = (occurrences.data ?? []).find(
    (item) => item.status === "SCHEDULED" || item.status === "DUE",
  );
  const nextCompletion = (completions.data ?? []).find((item) => item.occurrence_id === next?.id);
  const recentCompletion = (completions.data ?? [])[0];
  const conflictNotice =
    activity.status === "PAUSED" && recentCompletion?.completion_state === "MEDICATION_TAKEN"
      ? t.conflictConfirmedBeforePause
      : activity.status === "ENDED" && recentCompletion?.completion_state === "MEDICATION_TAKEN"
        ? t.conflictConfirmedBeforeEnd
        : null;

  const actionError =
    skip.error != null
      ? skip.error instanceof ApiError && skip.error.status === 409
        ? t.skipConflict
        : t.errorBody
      : pause.error != null || resume.error != null || end.error != null || update.error != null
        ? t.errorBody
        : null;

  function openEditModal() {
    setEditTitle(activity.display_title);
    setEditSubtitle(prescription?.dosage_information || activity.display_subtitle || "");
    setEditInstructions(prescription?.elder_friendly_description || "");
    setIsEditing(true);
  }

  return (
    <Screen>
      <TopAppBar title={t.details} showBack />

      {/* Main Info Card */}
      <Card accent={kind === "medication" ? "medication" : kind === "appointment" ? "info" : "none"}>
        <View style={styles.cardHeaderRow}>
          <View style={{ flex: 1 }}>
            <AppText variant="title">{activity.display_title}</AppText>
            <AppText variant="body" color={colors.textSecondary}>
              {prescription?.dosage_information || activity.display_subtitle}
            </AppText>
            {prescription?.elder_friendly_description ? (
              <AppText variant="caption" color={colors.textMuted}>
                {prescription.elder_friendly_description}
              </AppText>
            ) : null}
            <AppText variant="caption" color={colors.textMuted}>
              {careActivityStatusLabel(activity.status)}
            </AppText>
          </View>

          {canMutateMedication && activity.status !== "ENDED" ? (
            <Button label="ویرایش" variant="ghost" onPress={openEditModal} />
          ) : null}
        </View>
      </Card>

      {/* Edit Form Modal */}
      <Modal visible={isEditing} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <AppText variant="title">ویرایش مشخصات دارو</AppText>
            <TextField
              label="نام دارو"
              value={editTitle}
              onChangeText={setEditTitle}
              placeholder="مثلاً آسپرین"
            />
            <TextField
              label="دوز و دستور مصرف"
              value={editSubtitle}
              onChangeText={setEditSubtitle}
              placeholder="مثلاً ۱ عدد بعد از ناهار"
            />
            <TextField
              label="توضیح برای سالمند (خوانا و ساده)"
              value={editInstructions}
              onChangeText={setEditInstructions}
              placeholder="مثلاً قرص سفید کوچک بعد از غذا با یک لیوان آب"
            />
            {update.isError ? (
              <AppText variant="caption" color={colors.error}>
                {t.errorBody}
              </AppText>
            ) : null}
            <View style={styles.modalActions}>
              <Button
                label="ذخیره تغییرات"
                onPress={() => update.mutate()}
                loading={update.isPending}
                disabled={!editTitle.trim()}
              />
              <Button
                label={t.cancel}
                variant="secondary"
                onPress={() => setIsEditing(false)}
                disabled={update.isPending}
              />
            </View>
          </View>
        </View>
      </Modal>

      {/* End / Delete Confirmation Modal */}
      <Modal visible={showEndConfirm} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <AppText variant="title">پایان برنامه دارویی</AppText>
            <AppText variant="body" color={colors.textSecondary}>
              آیا از پایان این برنامه دارویی اطمینان دارید؟ نوبت‌های آینده لغو خواهند شد و تاریخچه مصرف قبلی محفوظ می‌ماند.
            </AppText>
            <View style={styles.modalActions}>
              <Button
                label="بله، پایان برنامه"
                variant="danger"
                onPress={() => end.mutate()}
                loading={end.isPending}
              />
              <Button
                label={t.cancel}
                variant="secondary"
                onPress={() => setShowEndConfirm(false)}
                disabled={end.isPending}
              />
            </View>
          </View>
        </View>
      </Modal>

      {conflictNotice ? (
        <Card accent="info">
          <AppText variant="caption" color={colors.textSecondary}>
            {conflictNotice}
          </AppText>
        </Card>
      ) : null}

      {next ? (
        <Card>
          <AppText variant="label">{t.next}</AppText>
          <AppText variant="time">{formatClock(next.scheduled_for)}</AppText>
          <AppText variant="caption" color={colors.textMuted}>
            {nextCompletion
              ? completionStateLabel(nextCompletion.completion_state)
              : next.status === "DUE"
                ? t.waitingForConfirmation
                : occurrenceStatusLabel(next.status)}
          </AppText>
          {canMutateMedication ? (
            <View style={styles.actions}>
              <Button
                label={t.skipOnce}
                variant="secondary"
                onPress={() => skip.mutate(next.id)}
                loading={skip.isPending}
              />
              <Button
                label={t.rescheduleOnce}
                variant="ghost"
                onPress={() =>
                  router.push({
                    pathname: "/(app)/program/confirm",
                    params: {
                      activityId,
                      occurrenceId: next.id,
                      scheduleId: activity.schedule_definition_id,
                      originalTime: next.scheduled_for,
                      kind: "reschedule",
                    },
                  })
                }
              />
            </View>
          ) : null}
        </Card>
      ) : null}

      {actionError ? (
        <AppText variant="caption" color={colors.error}>
          {actionError}
        </AppText>
      ) : null}

      {canMutateMedication ? (
        <View style={styles.actions}>
          {activity.status === "ACTIVE" ? (
            <Button
              label={t.pause}
              variant="secondary"
              onPress={() => pause.mutate()}
              loading={pause.isPending}
            />
          ) : null}
          {activity.status === "PAUSED" ? (
            <Button label={t.resume} onPress={() => resume.mutate()} loading={resume.isPending} />
          ) : null}
          {activity.status !== "ENDED" ? (
            <Button
              label="پایان برنامه دارویی"
              variant="danger"
              onPress={() => setShowEndConfirm(true)}
              loading={end.isPending}
            />
          ) : null}
        </View>
      ) : (
        <AppText variant="caption" color={colors.textMuted}>
          {isMedication ? t.medicationOnlyHint : "تغییر برنامه‌های غیر دارویی از این برنامه انجام نمی‌شود."}
        </AppText>
      )}

      <AppText variant="title">{t.history}</AppText>
      {(completions.data ?? []).slice(0, 8).map((item) => (
        <Card key={item.id}>
          <AppText variant="label">{completionStateLabel(item.completion_state)}</AppText>
          <AppText variant="caption">{formatRelative(item.interpreted_at)}</AppText>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  cardHeaderRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: spacing.sm,
  },
  actions: { gap: spacing.sm, marginVertical: spacing.md },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: spacing.screen,
  },
  modalContent: {
    width: "100%",
    maxWidth: 440,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.lg,
    gap: spacing.md,
  },
  modalActions: {
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
});
