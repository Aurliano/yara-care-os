import { Modal, Pressable, StyleSheet, View } from "react-native";
import {
  AppText,
  Button,
  Card,
  ErrorState,
  LoadingSkeleton,
  Screen,
  StatusBadge,
  TopAppBar,
} from "../../src/components";
import { entitlementLabel, t, toPersianDigits } from "../../src/i18n";
import { colors, radius, spacing } from "../../src/theme/tokens";
import { useElderStore } from "../../src/stores/elderStore";
import { useSubscription } from "../../src/hooks/useSubscription";
import { formatPrice, intervalLabel } from "../../src/services/licensing/subscriptionRepository";

export default function SubscriptionScreen() {
  const elderId = useElderStore((s) => s.selectedElderId);
  const {
    presentation,
    plans,
    entitlements,
    isLoading,
    isRefetching,
    isError,
    selectedPlanCode,
    setSelectedPlanCode,
    selectedInterval,
    setSelectedInterval,
    paymentState,
    checkoutResponse,
    errorMessage,
    isCheckoutLoading,
    canManageSubscription,
    handleReviewOrder,
    handleProceedToPayment,
    handleCancelReview,
    refetchAuthoritativeState,
  } = useSubscription(elderId);

  if (isLoading) {
    return (
      <Screen>
        <TopAppBar title={t.subscription} showBack />
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (isError && !presentation.license) {
    return (
      <Screen>
        <TopAppBar title={t.subscription} showBack />
        <ErrorState onRetry={refetchAuthoritativeState} />
      </Screen>
    );
  }

  const entitlementEntries = Object.entries(entitlements);
  const activePlans = plans.filter((p) => p.status === "ACTIVE");
  const isReviewModalVisible = paymentState === "REVIEW_DIALOG" && Boolean(checkoutResponse);

  return (
    <Screen>
      <TopAppBar title={t.subscription} showBack />

      {/* Permission guard notification for non-primary caregivers */}
      {!canManageSubscription ? (
        <Card style={styles.noticeCard}>
          <AppText variant="caption" color={colors.textSecondary}>
            {t.readOnlySubscriptionNotice}
          </AppText>
        </Card>
      ) : null}

      {/* Current License Status Card */}
      <Card style={styles.statusCard}>
        <View style={styles.statusHeader}>
          <View style={styles.planInfo}>
            <AppText variant="label" color={colors.textMuted}>
              {t.currentPlan}
            </AppText>
            <AppText variant="title">
              {presentation.planName ?? t.noActiveSubscription}
            </AppText>
          </View>
          <StatusBadge
            label={presentation.statusLabel}
            tone={presentation.statusTone}
          />
        </View>

        {presentation.validUntilFormatted ? (
          <View style={styles.validityRow}>
            <AppText variant="caption" color={colors.textMuted}>
              {t.validUntil}:
            </AppText>
            <AppText variant="label">
              {presentation.validUntilFormatted}
            </AppText>
          </View>
        ) : null}
      </Card>

      {/* Gateway Returning / Verifying Banner */}
      {paymentState === "VERIFYING" || paymentState === "PAYMENT_PENDING" ? (
        <Card style={styles.verifyingCard}>
          <AppText variant="label" color={colors.secondary}>
            {t.paymentVerifying}
          </AppText>
          <AppText variant="caption" color={colors.textSecondary}>
            {t.paymentVerifyingDesc}
          </AppText>
          <Button
            label={t.paymentPendingManualCheck}
            variant="secondary"
            loading={isRefetching}
            onPress={refetchAuthoritativeState}
            style={styles.verifyBtn}
          />
        </Card>
      ) : null}

      {/* Error state if checkout failed */}
      {paymentState === "CHECKOUT_ERROR" && errorMessage ? (
        <Card style={styles.errorCard}>
          <AppText variant="body" color={colors.error}>
            {errorMessage}
          </AppText>
        </Card>
      ) : null}

      {/* Plan selection and purchase for authorized caregivers */}
      {canManageSubscription ? (
        <View style={styles.section}>
          <AppText variant="title">{t.availablePlans}</AppText>

          {/* Billing Interval Toggle */}
          <View style={styles.intervalRow}>
            <Pressable
              accessibilityRole="button"
              onPress={() => setSelectedInterval("MONTHLY")}
              style={[
                styles.intervalPill,
                selectedInterval === "MONTHLY" && styles.intervalPillActive,
              ]}
            >
              <AppText
                variant="label"
                color={
                  selectedInterval === "MONTHLY"
                    ? colors.primaryOn
                    : colors.textSecondary
                }
              >
                {t.intervalMonthly}
              </AppText>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => setSelectedInterval("ANNUAL")}
              style={[
                styles.intervalPill,
                selectedInterval === "ANNUAL" && styles.intervalPillActive,
              ]}
            >
              <AppText
                variant="label"
                color={
                  selectedInterval === "ANNUAL"
                    ? colors.primaryOn
                    : colors.textSecondary
                }
              >
                {t.intervalAnnual}
              </AppText>
            </Pressable>
          </View>

          {/* Plan Cards */}
          <View style={styles.planList}>
            {activePlans.map((plan) => {
              const isSelected = selectedPlanCode === plan.code;
              return (
                <Pressable
                  key={plan.id}
                  accessibilityRole="button"
                  onPress={() => setSelectedPlanCode(plan.code)}
                >
                  <Card
                    style={isSelected ? styles.planCardSelected : styles.planCard}
                  >
                    <View style={styles.planRow}>
                      <View style={styles.planTitleCol}>
                        <AppText variant="bodyStrong">{plan.name}</AppText>
                        <AppText variant="caption" color={colors.textMuted}>
                          {plan.code}
                        </AppText>
                      </View>
                      {isSelected ? (
                        <StatusBadge label={t.selected} tone="success" />
                      ) : null}
                    </View>
                  </Card>
                </Pressable>
              );
            })}
          </View>

          {/* Action: Review Order */}
          <Button
            label={t.reviewOrder}
            variant="primary"
            loading={isCheckoutLoading}
            disabled={isCheckoutLoading || !selectedPlanCode}
            onPress={() => handleReviewOrder()}
            style={styles.reviewBtn}
          />
        </View>
      ) : null}

      {/* Review Dialog Modal: Server-Authoritative Price Display */}
      <Modal
        visible={isReviewModalVisible}
        transparent
        animationType="fade"
        onRequestClose={handleCancelReview}
      >
        <View style={styles.modalOverlay}>
          <Card style={styles.modalCard}>
            <AppText variant="title" align="center">
              {t.reviewOrderTitle}
            </AppText>
            <AppText
              variant="caption"
              color={colors.textMuted}
              align="center"
              style={styles.modalSubtitle}
            >
              {t.reviewOrderSubtitle}
            </AppText>

            <View style={styles.reviewDetails}>
              <View style={styles.detailRow}>
                <AppText variant="body" color={colors.textMuted}>
                  {t.currentPlan}:
                </AppText>
                <AppText variant="bodyStrong">
                  {plans.find((p) => p.code === selectedPlanCode)?.name ??
                    selectedPlanCode}
                </AppText>
              </View>

              <View style={styles.detailRow}>
                <AppText variant="body" color={colors.textMuted}>
                  {t.billingInterval}:
                </AppText>
                <AppText variant="bodyStrong">
                  {intervalLabel(selectedInterval)}
                </AppText>
              </View>

              {checkoutResponse ? (
                <View style={[styles.detailRow, styles.priceRow]}>
                  <AppText variant="bodyStrong">{t.pricePayable}:</AppText>
                  <AppText
                    variant="title"
                    color={colors.primary}
                  >
                    {formatPrice(
                      checkoutResponse.amount,
                      checkoutResponse.currency,
                    )}
                  </AppText>
                </View>
              ) : null}
            </View>

            <View style={styles.modalActions}>
              <Button
                label={t.proceedToPayment}
                variant="primary"
                onPress={handleProceedToPayment}
              />
              <Button
                label={t.cancelOrder}
                variant="ghost"
                onPress={handleCancelReview}
              />
            </View>
          </Card>
        </View>
      </Modal>

      {/* Active Entitlements Card */}
      <View style={styles.section}>
        <AppText variant="title">{t.entitlements}</AppText>
        <Card>
          {entitlementEntries.map(([key, value]) => (
            <View key={key} style={styles.entitlementRow}>
              <AppText variant="body">{entitlementLabel(key)}</AppText>
              <AppText variant="label">
                {typeof value === "boolean"
                  ? value
                    ? t.entitlementOn
                    : t.entitlementOff
                  : toPersianDigits(typeof value === "number" ? value : String(value ?? "—"))}
              </AppText>
            </View>
          ))}
          {!entitlementEntries.length ? (
            <AppText variant="body" color={colors.textSecondary}>
              {t.empty}
            </AppText>
          ) : null}
        </Card>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  noticeCard: {
    backgroundColor: colors.surfaceMuted,
    marginBottom: spacing.md,
  },
  statusCard: {
    marginBottom: spacing.lg,
    padding: spacing.md,
  },
  statusHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  planInfo: { gap: spacing.xs },
  validityRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginTop: spacing.md,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderMuted,
  },
  verifyingCard: {
    backgroundColor: colors.surfaceMuted,
    gap: spacing.sm,
    marginBottom: spacing.lg,
    padding: spacing.md,
  },
  verifyBtn: {
    marginTop: spacing.xs,
  },
  errorCard: {
    backgroundColor: colors.errorSoft,
    marginBottom: spacing.md,
  },
  section: {
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  intervalRow: {
    flexDirection: "row",
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.pill,
    padding: 4,
    gap: spacing.xs,
    marginVertical: spacing.xs,
  },
  intervalPill: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
  },
  intervalPillActive: {
    backgroundColor: colors.primary,
  },
  planList: {
    gap: spacing.sm,
  },
  planCard: {
    borderWidth: 1,
    borderColor: colors.border,
  },
  planCardSelected: {
    borderWidth: 2,
    borderColor: colors.primary,
    backgroundColor: colors.surface,
  },
  planRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  planTitleCol: {
    gap: 2,
  },
  reviewBtn: {
    marginTop: spacing.sm,
  },
  entitlementRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: spacing.sm,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: spacing.screen,
  },
  modalCard: {
    width: "100%",
    maxWidth: 400,
    padding: spacing.lg,
    gap: spacing.md,
  },
  modalSubtitle: {
    marginTop: -spacing.xs,
  },
  reviewDetails: {
    gap: spacing.sm,
    marginVertical: spacing.sm,
  },
  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: spacing.xs,
  },
  priceRow: {
    borderTopWidth: 1,
    borderTopColor: colors.borderMuted,
    paddingTop: spacing.sm,
    marginTop: spacing.xs,
  },
  modalActions: {
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
});
