import { StyleSheet, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { AppText, Card, ErrorState, LoadingSkeleton, Screen, TopAppBar } from "../../src/components";
import { entitlementLabel, t, toPersianDigits } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import { getEntitlements } from "../../src/api/endpoints/licensing";
import { queryKeys } from "../../src/api/queryKeys";
import { useElderStore } from "../../src/stores/elderStore";

export default function SubscriptionScreen() {
  const elderId = useElderStore((s) => s.selectedElderId);
  const entitlements = useQuery({
    queryKey: elderId ? queryKeys.entitlements(elderId) : ["entitlements"],
    enabled: Boolean(elderId),
    queryFn: () => getEntitlements(elderId as string),
  });

  if (entitlements.isPending) {
    return (
      <Screen>
        <TopAppBar title={t.subscription} showBack />
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (entitlements.isError && !entitlements.data) {
    return (
      <Screen>
        <TopAppBar title={t.subscription} showBack />
        <ErrorState onRetry={() => void entitlements.refetch()} />
      </Screen>
    );
  }

  const entries = Object.entries(entitlements.data?.entitlements ?? {});

  return (
    <Screen>
      <TopAppBar title={t.subscription} showBack />
      <AppText variant="caption" color={colors.textMuted}>
        {t.subscriptionReadOnly}
      </AppText>
      <AppText variant="title">{t.entitlements}</AppText>
      <Card>
        {entries.map(([key, value]) => (
          <View key={key} style={styles.row}>
            <AppText variant="body">{entitlementLabel(key)}</AppText>
            <AppText variant="label">
              {typeof value === "boolean"
                ? value
                  ? t.entitlementOn
                  : t.entitlementOff
                : toPersianDigits(value ?? "—")}
            </AppText>
          </View>
        ))}
        {!entries.length ? (
          <AppText variant="body" color={colors.textSecondary}>
            {t.empty}
          </AppText>
        ) : null}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", paddingVertical: spacing.sm },
});
