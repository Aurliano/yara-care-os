import { Pressable, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { t } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import {
  AppText,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Screen,
  TopAppBar,
} from "../../../src/components";
import { loadAlertInbox } from "../../../src/services/alerts/alertRepository";
import { queryKeys } from "../../../src/api/queryKeys";
import { useElderStore } from "../../../src/stores/elderStore";

export default function AlertsScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const query = useQuery({
    queryKey: elderId ? queryKeys.alerts(elderId) : ["alerts"],
    enabled: Boolean(elderId),
    queryFn: () => loadAlertInbox(elderId as string),
  });

  if (query.isPending) {
    return (
      <Screen>
        <TopAppBar title={t.alertsTitle} showBack />
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (query.isError) {
    return (
      <Screen>
        <TopAppBar title={t.alertsTitle} showBack />
        <ErrorState onRetry={() => void query.refetch()} />
      </Screen>
    );
  }

  const inbox = query.data;
  if (!inbox?.available) {
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

  return (
    <Screen>
      <TopAppBar title={t.alertsTitle} showBack />
      <AppText variant="body" color={colors.textSecondary}>
        {t.alertsSubtitle}
      </AppText>
      {inbox.items.length === 0 ? (
        <EmptyState title={t.alertsEmptyTitle} body={t.alertsEmptyBody} />
      ) : (
        inbox.items.map((alert) => (
          <Pressable
            key={alert.id}
            style={styles.item}
            onPress={() => router.push(`/(app)/alerts/${alert.id}`)}
          >
            <Card accent={alert.severity === "urgent" ? "error" : "warning"}>
              <AppText variant="label">{alert.title}</AppText>
              <AppText variant="caption" color={colors.textSecondary}>
                {alert.body}
              </AppText>
            </Card>
          </Pressable>
        ))
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  item: {
    marginTop: spacing.sm,
  },
});
