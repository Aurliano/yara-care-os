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
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";

export default function DevicesScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can, isPending } = usePermissions();
  const query = useQuery({
    queryKey: elderId ? queryKeys.devices(elderId) : ["devices"],
    enabled: Boolean(elderId),
    queryFn: () => loadElderDevices(elderId as string),
  });

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
    return (
      <Screen>
        <TopAppBar title={t.devicesTitle} />
        <ErrorState onRetry={() => void query.refetch()} />
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
        <EmptyState title={t.devicesEmptyTitle} body={t.devicesEmptyBody} />
      ) : (
        items.map((device) => (
          <Pressable key={device.id} onPress={() => router.push(`/(app)/devices/${device.id}`)}>
            <Card>
              <View style={styles.row}>
                <View style={{ flex: 1 }}>
                  <AppText variant="label">{device.kind === "HUB" ? t.hubYara : device.kind === "PILLBOX" ? t.pillBox : t.devicesTitle}</AppText>
                  <AppText variant="caption" color={colors.textSecondary}>
                    {device.batteryPercent === null
                      ? t.batteryUnknown
                      : `${t.charge} ${toPersianDigits(device.batteryPercent)}٪`}
                  </AppText>
                </View>
                <StatusBadge
                  label={isDeviceConnected(device.connectivity) ? t.online : t.disconnected}
                  tone={isDeviceConnected(device.connectivity) ? "success" : "error"}
                />
              </View>
            </Card>
          </Pressable>
        ))
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
