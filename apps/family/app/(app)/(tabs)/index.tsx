import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../src/api/queryKeys";
import { isPermissionDenied } from "../../../src/api/errors";
import {
  AppText,
  Avatar,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  PermissionDenied,
  Screen,
  SetupActions,
  StatusBadge,
  StaleBanner,
  TopAppBar,
} from "../../../src/components";
import { StatusHero } from "../../../src/components/StatusHero";
import { Icon } from "../../../src/components/Icon";
import { t, formatClock, formatRelative } from "../../../src/i18n";
import { composeDashboard } from "../../../src/services/dashboard/composeDashboard";
import { hasEntitlement } from "../../../src/services/licensing/entitlements";
import { useElderStore } from "../../../src/stores/elderStore";
import { colors, radius, spacing } from "../../../src/theme/tokens";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { usePermissions } from "../../../src/permissions/usePermission";

export default function HomeScreen() {
  const router = useRouter();
  const elderId = useElderStore((state) => state.selectedElderId);
  const { can, isPending: permissionsPending } = usePermissions();
  const query = useQuery({
    queryKey: elderId ? queryKeys.dashboard(elderId) : ["dashboard", "none"],
    queryFn: () => composeDashboard(elderId as string),
    enabled: Boolean(elderId),
  });

  if (!permissionsPending && !can(PERMISSIONS.VIEW_ELDER_STATUS)) {
    return <PermissionDenied />;
  }

  if (query.isPending) {
    return (
      <Screen>
        <TopAppBar />
        <LoadingSkeleton rows={4} />
      </Screen>
    );
  }

  if (query.isError && isPermissionDenied(query.error)) {
    return <PermissionDenied />;
  }

  if (query.isError && !query.data) {
    return (
      <Screen>
        <TopAppBar />
        <ErrorState onRetry={() => void query.refetch()} />
      </Screen>
    );
  }

  const data = query.data;
  if (!data) {
    return null;
  }

  const stale = query.isError || (query.isFetched && query.isStale && query.fetchStatus === "paused");
  const updatedAt = data.freshness.kind === "unavailable" ? null : data.freshness.updatedAt;
  const freshnessLabel = updatedAt ? formatRelative(updatedAt) : t.unknownValue;
  const tone = stale ? "unknown" : data.tone;
  const showPillbox = hasEntitlement(data.entitlements, "PILLBOX_SUPPORT");

  return (
    <Screen>
      <TopAppBar />
      <View style={styles.profile}>
        <View>
          <AppText variant="caption" color={colors.textSecondary}>
            {t.lastUpdated}
          </AppText>
          <AppText variant="label" color={colors.primary}>
            {stale ? t.staleTitle : freshnessLabel}
          </AppText>
        </View>
        <View style={styles.profileRight}>
          <View>
            <AppText variant="title">{data.elder.full_name}</AppText>
          </View>
          <Avatar name={data.elder.full_name} />
        </View>
      </View>

      {stale && updatedAt ? <StaleBanner updatedLabel={formatRelative(updatedAt)} /> : null}

      {data.setupRequired && !stale ? (
        <>
          <EmptyState title={t.firstSetupTitle} body={t.firstSetupBody} />
          <SetupActions
            onAddMedication={() => router.push("/(app)/program/add?kind=medication")}
            onAddAppointment={() => router.push("/(app)/program/add?kind=appointment")}
            onConnectDevice={() => router.push("/(app)/(tabs)/devices")}
          />
        </>
      ) : (
        <StatusHero tone={tone} elderName={data.elder.full_name} count={data.topAction ? 1 : 0} />
      )}

      {data.topAction && !stale ? (
        <Card accent="error">
          <AppText variant="label">{data.topAction.activity.display_title}</AppText>
          <AppText variant="caption" color={colors.textSecondary}>
            {formatClock(data.topAction.occurrence.scheduled_for)}
          </AppText>
          <Pressable onPress={() => router.push("/(app)/(tabs)/program")} style={styles.cta}>
            <AppText variant="label" color={colors.primaryOn} align="center">
              {t.viewFollow}
            </AppText>
          </Pressable>
        </Card>
      ) : null}

      <AppText variant="title">{t.todayProgram}</AppText>
      {data.today.length === 0 ? (
        data.setupRequired ? null : (
          <Card>
            <AppText variant="body" color={colors.textSecondary}>
              {t.emptyTodayProgram}
            </AppText>
          </Card>
        )
      ) : (
        data.today.slice(0, 4).map((item) => (
          <Pressable
            key={item.occurrence.id}
            onPress={() => router.push(`/(app)/program/${item.activity.id}`)}
          >
            <Card>
              <View style={styles.row}>
                <AppText variant="time" color={colors.primary}>
                  {formatClock(item.occurrence.scheduled_for)}
                </AppText>
                <View style={{ flex: 1 }}>
                  <AppText variant="label">{item.activity.display_title}</AppText>
                  <AppText variant="body" color={colors.textSecondary}>
                    {item.prescription?.dosage_information || item.activity.display_subtitle}
                  </AppText>
                </View>
                <Icon name="pill_small" width={14} height={18} />
              </View>
            </Card>
          </Pressable>
        ))
      )}

      <AppText variant="title">{t.deviceStatus}</AppText>
      {data.devices.available ? (
        <View style={styles.deviceRow}>
          {data.devices.items
            .filter((device) => device.kind !== "PILLBOX" || showPillbox)
            .map((device) => (
              <Pressable key={device.id} style={{ flex: 1 }} onPress={() => router.push("/(app)/(tabs)/devices")}>
                <Card>
                  <AppText variant="label" align="center">
                    {device.kind === "HUB" ? t.hub : t.pillBox}
                  </AppText>
                  <StatusBadge
                    label={device.connectivity === "online" ? t.online : t.disconnected}
                    tone={device.connectivity === "online" ? "success" : "error"}
                  />
                </Card>
              </Pressable>
            ))}
        </View>
      ) : (
        <Card>
          <AppText variant="body" color={colors.textSecondary}>
            {t.devicesUnavailableBody}
          </AppText>
          <Pressable onPress={() => router.push("/(app)/(tabs)/devices")}>
            <AppText variant="label" color={colors.primary}>
              {t.navDevices}
            </AppText>
          </Pressable>
        </Card>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  profile: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: spacing.md,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.lg,
  },
  profileRight: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  cta: {
    marginTop: spacing.md,
    backgroundColor: colors.primary,
    borderRadius: radius.pill,
    minHeight: 44,
    justifyContent: "center",
  },
  deviceRow: { flexDirection: "row", gap: spacing.sm },
});
