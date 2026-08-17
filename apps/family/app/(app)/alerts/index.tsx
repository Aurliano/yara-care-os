import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { t } from "../../../src/i18n";
import { EmptyState, Screen, TopAppBar } from "../../../src/components";
import { loadAlertInbox } from "../../../src/services/alerts/alertRepository";
import { queryKeys } from "../../../src/api/queryKeys";
import { useElderStore } from "../../../src/stores/elderStore";

export default function AlertsScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  useQuery({
    queryKey: elderId ? queryKeys.alerts(elderId) : ["alerts"],
    enabled: Boolean(elderId),
    queryFn: () => loadAlertInbox(elderId as string),
  });

  return (
    <Screen>
      <TopAppBar title={t.alertsTitle} showBack />
      <EmptyState
        title={t.alertsUnavailableTitle}
        body={t.alertsUnavailableBody}
        actionLabel={t.backHome}
        onAction={() => router.replace("/(app)/(tabs)")}
      />
    </Screen>
  );
}
