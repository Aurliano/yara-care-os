import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { AppText, Button, Card, EmptyState, Screen, TopAppBar } from "../../../src/components";
import { t } from "../../../src/i18n";
import { colors } from "../../../src/theme/tokens";
import { getAlertById, loadAlertInbox } from "../../../src/services/alerts/alertRepository";
import { useElderStore } from "../../../src/stores/elderStore";
import { useAlertAckStore } from "../../../src/stores/alertAckStore";
import { queryKeys } from "../../../src/api/queryKeys";
import { firstParam } from "../../../src/navigation/params";

export default function AlertDetailScreen() {
  const params = useLocalSearchParams<{ alertId: string }>();
  const alertId = firstParam(params.alertId);
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const acknowledge = useAlertAckStore((s) => s.acknowledge);
  const isAcknowledged = useAlertAckStore((s) => (alertId ? s.isAcknowledged(alertId) : false));
  useQuery({
    queryKey: elderId ? queryKeys.alerts(elderId) : ["alerts"],
    queryFn: () => loadAlertInbox(elderId as string),
    enabled: Boolean(elderId),
  });
  const detail = useQuery({
    queryKey: ["alert", alertId],
    queryFn: () => getAlertById(elderId as string, alertId as string),
    enabled: Boolean(elderId && alertId),
  });

  return (
    <Screen>
      <TopAppBar title={t.alertsTitle} showBack showBell={false} />
      {detail.data ? (
        <Card accent={detail.data.severity === "urgent" ? "error" : "warning"}>
          <AppText variant="title">{detail.data.title}</AppText>
          <AppText variant="body" color={colors.textSecondary}>
            {detail.data.body}
          </AppText>
          <AppText variant="caption">{t.acknowledgeHint}</AppText>
          <Button
            label={isAcknowledged ? t.seen : t.acknowledge}
            disabled={isAcknowledged}
            onPress={() => {
              if (alertId) void acknowledge(alertId);
            }}
          />
        </Card>
      ) : (
        <EmptyState
          title={t.alertsUnavailableTitle}
          body={t.alertsUnavailableBody}
          actionLabel={t.backHome}
          onAction={() => router.replace("/(app)/(tabs)/alerts")}
        />
      )}
    </Screen>
  );
}
