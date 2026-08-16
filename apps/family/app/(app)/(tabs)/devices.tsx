import { StyleSheet, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { t } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import { AppText, Card, EmptyState, LoadingSkeleton, Screen, TopAppBar } from "../../../src/components";
import { loadElderDevices } from "../../../src/services/devices/deviceRepository";
import { queryKeys } from "../../../src/api/queryKeys";
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";

export default function DevicesScreen() {
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

  return (
    <Screen>
      <TopAppBar title={t.devicesTitle} />
      <AppText variant="body" color={colors.textSecondary}>
        {t.devicesSubtitle}
      </AppText>
      <EmptyState title={t.devicesUnavailableTitle} body={t.devicesUnavailableBody} />
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
  hint: { marginTop: spacing.md },
});
