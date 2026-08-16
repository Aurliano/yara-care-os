import { StyleSheet, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { AppText, Card, ErrorState, LoadingSkeleton, Screen, TopAppBar } from "../../src/components";
import { t, formatPersianDate, toPersianDigits } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import { getElderLicense, getEntitlements } from "../../src/api/endpoints/licensing";
import { queryKeys } from "../../src/api/queryKeys";
import { useElderStore } from "../../src/stores/elderStore";
import { usePermissions } from "../../src/permissions/usePermission";
import { PERMISSIONS } from "../../src/permissions/codes";
import { ApiError } from "../../src/api/errors";

export default function SubscriptionScreen() {
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();
  const license = useQuery({
    queryKey: elderId ? queryKeys.license(elderId) : ["license"],
    enabled: Boolean(elderId),
    queryFn: () => getElderLicense(elderId as string),
  });
  const entitlements = useQuery({
    queryKey: elderId ? queryKeys.entitlements(elderId) : ["entitlements"],
    enabled: Boolean(elderId),
    queryFn: () => getEntitlements(elderId as string),
  });

  if (license.isPending || entitlements.isPending) {
    return (
      <Screen>
        <LoadingSkeleton />
      </Screen>
    );
  }

  const missing = license.isError && license.error instanceof ApiError && license.error.status === 404;

  return (
    <Screen>
      <TopAppBar title={t.subscription} showBack showBell={false} />
      <AppText variant="caption" color={colors.textMuted}>
        {t.subscriptionReadOnly}
      </AppText>
      {missing ? (
        <Card>
          <AppText variant="body">{t.empty}</AppText>
        </Card>
      ) : license.isError ? (
        <ErrorState onRetry={() => void license.refetch()} />
      ) : (
        <Card>
          <AppText variant="title">{license.data?.plan_code}</AppText>
          <AppText variant="caption">{license.data?.status}</AppText>
          <AppText variant="body" color={colors.textSecondary}>
            {license.data?.valid_until ? formatPersianDate(license.data.valid_until) : t.unknownValue}
          </AppText>
        </Card>
      )}
      <AppText variant="title">{t.entitlements}</AppText>
      <Card>
        {Object.entries(entitlements.data?.entitlements ?? {}).map(([key, value]) => (
          <View key={key} style={styles.row}>
            <AppText variant="body">{key}</AppText>
            <AppText variant="label">
              {typeof value === "boolean" ? (value ? "فعال" : "غیرفعال") : toPersianDigits(value ?? "—")}
            </AppText>
          </View>
        ))}
        {!Object.keys(entitlements.data?.entitlements ?? {}).length ? (
          <AppText variant="body" color={colors.textSecondary}>
            {t.empty}
          </AppText>
        ) : null}
      </Card>
      {can(PERMISSIONS.MANAGE_SUBSCRIPTION) ? (
        <AppText variant="caption" color={colors.textMuted}>
          تغییر طرح فقط از طریق API مجاز سرور و با مجوز مدیریت اشتراک انجام می‌شود. رابط پرداخت در سرور موجود نیست.
        </AppText>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", paddingVertical: spacing.sm },
});
