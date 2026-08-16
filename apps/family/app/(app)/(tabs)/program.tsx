import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../src/api/queryKeys";
import { listCareActivities, listPrescriptions } from "../../../src/api/endpoints/care";
import { listOccurrences } from "../../../src/api/endpoints/scheduling";
import { endOfLocalDay, startOfLocalDay } from "../../../src/i18n/dates";
import { t, formatClock, formatPersianDate } from "../../../src/i18n";
import { colors, radius, spacing } from "../../../src/theme/tokens";
import {
  AppText,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Screen,
  SetupActions,
  TopAppBar,
} from "../../../src/components";
import { Icon } from "../../../src/components/Icon";
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { visualKindFor } from "../../../src/services/program/activityKind";
import type { CareActivity, Occurrence, Prescription } from "../../../src/api/types";

export default function ProgramScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();
  const query = useQuery({
    queryKey: elderId ? [...queryKeys.careActivities(elderId), "today-program"] : ["program"],
    enabled: Boolean(elderId),
    queryFn: async () => {
      const [activities, prescriptions] = await Promise.all([
        listCareActivities(elderId as string),
        listPrescriptions(elderId as string),
      ]);
      const start = startOfLocalDay().toISOString();
      const end = endOfLocalDay().toISOString();
      const items: { activity: CareActivity; occurrence: Occurrence; prescription?: Prescription }[] = [];
      await Promise.all(
        activities.map(async (activity) => {
          const occ = await listOccurrences(activity.schedule_definition_id, {
            type: "between",
            start,
            end,
          }).catch(() => [] as Occurrence[]);
          const list = Array.isArray(occ) ? occ : occ ? [occ] : [];
          for (const occurrence of list) {
            items.push({
              activity,
              occurrence,
              prescription: prescriptions.find((p) => p.care_activity_id === activity.id),
            });
          }
        }),
      );
      items.sort(
        (a, b) =>
          new Date(a.occurrence.scheduled_for).getTime() - new Date(b.occurrence.scheduled_for).getTime(),
      );
      return { activities, items };
    },
  });

  if (query.isPending) {
    return (
      <Screen>
        <TopAppBar title={t.programTitle} />
        <LoadingSkeleton />
      </Screen>
    );
  }
  if (query.isError) {
    return (
      <Screen>
        <TopAppBar title={t.programTitle} />
        <ErrorState onRetry={() => void query.refetch()} />
      </Screen>
    );
  }

  const data = query.data;
  const emptyToday = !data?.items.length;
  const setupRequired = !data?.activities.length;

  return (
    <Screen>
      <TopAppBar title={t.programTitle} />
      <View style={styles.tabs}>
        <View style={[styles.tab, styles.tabActive]}>
          <AppText variant="label" color={colors.primary} align="center">
            {t.today}
          </AppText>
        </View>
        <View style={styles.tab}>
          <AppText variant="label" color={colors.textSecondary} align="center">
            {t.week}
          </AppText>
        </View>
        <View style={styles.tab}>
          <AppText variant="label" color={colors.textSecondary} align="center">
            {t.calendar}
          </AppText>
        </View>
      </View>
      <AppText variant="title">{formatPersianDate(new Date())}</AppText>
      <AppText variant="caption" color={colors.textMuted}>
        {t.today}
      </AppText>
      {setupRequired ? (
        <>
          <EmptyState title={t.firstSetupTitle} body={t.firstSetupBody} />
          <SetupActions
            onAddMedication={() => router.push("/(app)/program/add?kind=medication")}
            onAddAppointment={() => router.push("/(app)/program/add?kind=appointment")}
            onConnectDevice={() => router.push("/(app)/(tabs)/devices")}
          />
        </>
      ) : emptyToday ? (
        <EmptyState title={t.empty} body={t.emptyTodayProgram} />
      ) : (
        (data?.items ?? []).map((item) => {
          const kind = visualKindFor(item.activity.activity_type, item.activity.display_title);
          return (
            <Pressable
              key={item.occurrence.id}
              onPress={() => router.push(`/(app)/program/${item.activity.id}`)}
            >
              <Card accent={kind === "medication" ? "medication" : kind === "appointment" ? "info" : "none"}>
                <View style={styles.row}>
                  <View style={{ flex: 1 }}>
                    <AppText variant="label">{item.activity.display_title}</AppText>
                    <AppText variant="body" color={colors.textSecondary}>
                      {item.prescription?.elder_friendly_description || item.activity.display_subtitle}
                    </AppText>
                  </View>
                  <AppText variant="time">{formatClock(item.occurrence.scheduled_for)}</AppText>
                </View>
              </Card>
            </Pressable>
          );
        })
      )}
      {can(PERMISSIONS.MANAGE_MEDICATION) && !setupRequired ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t.addMedication}
          onPress={() => router.push("/(app)/program/add?kind=medication")}
          style={styles.fab}
        >
          <Icon name="plus" color={colors.primaryOn} width={14} height={14} />
        </Pressable>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  tabs: {
    flexDirection: "row",
    backgroundColor: colors.surfaceSoft,
    borderRadius: radius.sm,
    padding: 4,
    marginBottom: spacing.md,
  },
  tab: { flex: 1, paddingVertical: spacing.sm, borderRadius: 4 },
  tabActive: { backgroundColor: colors.background },
  row: { flexDirection: "row", gap: spacing.md, alignItems: "flex-start" },
  fab: {
    position: "absolute",
    left: spacing.lg,
    bottom: 96,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
});
