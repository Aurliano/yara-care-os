import { useLocalSearchParams, useRouter } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { StyleSheet, View } from "react-native";
import {
  getCareActivity,
  listCompletions,
  pauseCareActivity,
  resumeCareActivity,
} from "../../../src/api/endpoints/care";
import { listOccurrences, skipOccurrence } from "../../../src/api/endpoints/scheduling";
import { AppText, Button, Card, ErrorState, LoadingSkeleton, Screen, TopAppBar } from "../../../src/components";
import { t, formatClock, formatRelative, careActivityStatusLabel, completionStateLabel, occurrenceStatusLabel } from "../../../src/i18n";
import { firstParam } from "../../../src/navigation/params";
import { colors, spacing } from "../../../src/theme/tokens";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { visualKindFor } from "../../../src/services/program/activityKind";
import { endOfLocalDay, startOfLocalDay } from "../../../src/i18n/dates";
import type { Occurrence } from "../../../src/api/types";

export default function ActivityDetailScreen() {
  const activityId = firstParam(useLocalSearchParams<{ activityId: string }>().activityId) ?? "";
  const router = useRouter();
  const queryClient = useQueryClient();
  const { can } = usePermissions();
  const query = useQuery({
    queryKey: ["care-activity", activityId],
    enabled: Boolean(activityId),
    queryFn: () => getCareActivity(activityId),
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

  const pause = useMutation({
    mutationFn: () => pauseCareActivity(activityId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["care-activity", activityId] }),
  });
  const resume = useMutation({
    mutationFn: () => resumeCareActivity(activityId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["care-activity", activityId] }),
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
  const next = occurrences.data?.[0];
  const nextCompletion = (completions.data ?? []).find((item) => item.occurrence_id === next?.id);

  return (
    <Screen>
      <TopAppBar title={t.details} showBack />
      <Card accent={kind === "medication" ? "medication" : kind === "appointment" ? "info" : "none"}>
        <AppText variant="title">{activity.display_title}</AppText>
        <AppText variant="body" color={colors.textSecondary}>
          {activity.display_subtitle}
        </AppText>
        <AppText variant="caption" color={colors.textMuted}>
          {careActivityStatusLabel(activity.status)}
        </AppText>
      </Card>

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
                onPress={() =>
                  void skipOccurrence(next.id).then(() =>
                    queryClient.invalidateQueries({ queryKey: ["care-activity", activityId] }),
                  )
                }
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

      {canMutateMedication ? (
        <View style={styles.actions}>
          {activity.status === "ACTIVE" ? (
            <Button label={t.pause} variant="secondary" onPress={() => pause.mutate()} loading={pause.isPending} />
          ) : null}
          {activity.status === "PAUSED" ? (
            <Button label={t.resume} onPress={() => resume.mutate()} loading={resume.isPending} />
          ) : null}
          {activity.status !== "ENDED" ? (
            <Button
              label={t.endActivity}
              variant="danger"
              onPress={() =>
                router.push({
                  pathname: "/(app)/program/confirm",
                  params: { activityId, kind: "end" },
                })
              }
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
  actions: { gap: spacing.sm, marginVertical: spacing.md },
});
