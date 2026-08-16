import { useLocalSearchParams, useRouter } from "expo-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppText, Button, Card, Screen, TopAppBar } from "../../../src/components";
import { t } from "../../../src/i18n";
import { colors } from "../../../src/theme/tokens";
import { createPairing, listPairings } from "../../../src/api/endpoints/device";
import { queryKeys } from "../../../src/api/queryKeys";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";
import { firstParam } from "../../../src/navigation/params";

export default function PairingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ hubId?: string; peripheralId?: string }>();
  const hubId = firstParam(params.hubId);
  const peripheralId = firstParam(params.peripheralId);
  const { can } = usePermissions();
  const pairings = useQuery({
    queryKey: hubId ? queryKeys.pairings(hubId) : ["pairings"],
    enabled: Boolean(hubId),
    queryFn: () => listPairings(hubId as string),
    refetchInterval: 3000,
  });
  const start = useMutation({
    mutationFn: () =>
      createPairing(hubId as string, {
        hub_device_id: hubId as string,
        peripheral_device_id: peripheralId as string,
      }),
  });

  if (!can(PERMISSIONS.MANAGE_DEVICES)) {
    return <PermissionDenied />;
  }

  const latest = pairings.data?.[0];
  const status = latest?.status ?? (start.isPending ? "PAIRING" : undefined);

  return (
    <Screen>
      <TopAppBar title={t.pairingPending} showBack showBell={false} />
      <Card>
        <AppText variant="title">
          {status === "ACTIVE"
            ? t.pairingSuccess
            : status === "PAIRING"
              ? t.pairingPending
              : status
                ? t.pairingFailed
                : t.devicesUnavailableTitle}
        </AppText>
        <AppText variant="body" color={colors.textSecondary}>
          {t.pairingHelp}
        </AppText>
        {hubId && peripheralId ? (
          <Button
            label={t.startRePair}
            onPress={() => start.mutate()}
            loading={start.isPending}
            variant="danger"
          />
        ) : (
          <AppText variant="caption" color={colors.textMuted}>
            {t.devicesUnavailableBody}
          </AppText>
        )}
        <Button label={t.notNow} variant="secondary" onPress={() => router.back()} />
      </Card>
    </Screen>
  );
}
