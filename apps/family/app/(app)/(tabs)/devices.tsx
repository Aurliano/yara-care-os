import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { t, toPersianDigits } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import {
  AppText,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Screen,
  StatusBadge,
  TopAppBar,
} from "../../../src/components";
import { loadElderDevices, isDeviceConnected } from "../../../src/services/devices/deviceRepository";
import { queryKeys } from "../../../src/api/queryKeys";
import { getAppErrorDisplay } from "../../../src/api/errors";
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";

function formatLastSeen(lastSeenAt: string | null): string {
  if (!lastSeenAt) return "هنوز متصل نشده";
  try {
    const diffMs = Date.now() - new Date(lastSeenAt).getTime();
    if (diffMs < 0 || diffMs < 60 * 1000) return "لحظاتی پیش";
    const minutes = Math.floor(diffMs / (60 * 1000));
    if (minutes < 60) return `${toPersianDigits(minutes)} دقیقه پیش`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${toPersianDigits(hours)} ساعت پیش`;
    const days = Math.floor(hours / 24);
    return `${toPersianDigits(days)} روز پیش`;
  } catch {
    return "نامشخص";
  }
}

export default function DevicesScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can, isPending } = usePermissions();
  const query = useQuery({
    queryKey: elderId ? queryKeys.devices(elderId) : ["devices"],
    enabled: Boolean(elderId),
    queryFn: () => loadElderDevices(elderId as string),
  });

  if (!elderId) {
    return (
      <Screen>
        <TopAppBar title={t.devicesTitle} />
        <EmptyState
          title={t.noElderTitle}
          body={t.noElderBody}
          actionLabel={t.setupElder}
          onAction={() => router.push("/(auth)/create-elder")}
        />
      </Screen>
    );
  }

  if (!isPending && !can(PERMISSIONS.VIEW_ELDER_STATUS)) {
    return <PermissionDenied />;
  }

  if (query.isPending) {
    return (
      <Screen>
        <TopAppBar title={t.devicesTitle} />
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (query.isError) {
    const errorDisplay = getAppErrorDisplay(query.error);
    return (
      <Screen>
        <TopAppBar title={t.devicesTitle} />
        <ErrorState
          title={errorDisplay.title}
          body={errorDisplay.body}
          onRetry={() => void query.refetch()}
        />
      </Screen>
    );
  }

  const catalog = query.data;
  const items = catalog?.available ? catalog.items : [];

  return (
    <Screen>
      <TopAppBar title={t.devicesTitle} />
      <AppText variant="body" color={colors.textSecondary}>
        {t.devicesSubtitle}
      </AppText>
      {items.length === 0 ? (
        <EmptyState
          title={t.devicesEmptyTitle}
          body={t.devicesEmptyBody}
          actionLabel="مشاهده محصولات و تجهیزات سایدا"
          onAction={() => router.push("/(app)/catalog" as never)}
        />
      ) : (
        items.map((device) => {
          const isOnline = isDeviceConnected(device.connectivity);
          return (
            <Pressable key={device.id} onPress={() => router.push(`/(app)/devices/${device.id}`)}>
              <Card>
                <View style={styles.row}>
                  <View style={{ flex: 1 }}>
                    <AppText variant="label">
                      {device.kind === "HUB" ? "همراه رومیزی سایدا (هاب)" : device.kind === "PILLBOX" ? t.pillBox : t.devicesTitle}
                    </AppText>
                    <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.xs, flexWrap: "wrap" }}>
                      <AppText variant="caption" color={colors.textSecondary}>
                        {device.batteryPercent === null
                          ? t.batteryUnknown
                          : `${t.charge}: ${toPersianDigits(device.batteryPercent)}٪`}
                      </AppText>
                      <AppText variant="caption" color={colors.textMuted}>
                        •
                      </AppText>
                      <AppText variant="caption" color={isOnline ? colors.success : colors.textMuted}>
                        {isOnline ? "متصل هم‌اکنون" : `آخرین اتصال: ${formatLastSeen(device.lastSeenAt)}`}
                      </AppText>
                    </View>
                  </View>
                  <StatusBadge
                    label={isOnline ? t.online : t.disconnected}
                    tone={isOnline ? "success" : "neutral"}
                  />
                </View>
              </Card>
            </Pressable>
          );
        })
      )}
      <Card>
        <AppText variant="caption" color={colors.textMuted}>
          {t.noRemoteOpen}
        </AppText>
      </Card>
      {can(PERMISSIONS.MANAGE_DEVICES) ? (
        <View style={styles.hint}>
          <AppText variant="caption" color={colors.textMuted}>
            {t.pairingHelp}
          </AppText>
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  hint: { marginTop: spacing.md },
});
