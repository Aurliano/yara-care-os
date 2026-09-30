import React from "react";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { colors, elevation, radius, sizes, spacing } from "../../src/theme/tokens";
import { AppText } from "../../src/components/AppText";
import { BrandLockup } from "../../src/components/BrandLockup";
import { Button } from "../../src/components/Button";
import { Card } from "../../src/components/Card";
import { Icon } from "../../src/components/Icon";
import {
  getProductById,
  defaultPricingProvider,
  type AcquisitionMethod,
  type SubscriptionTier,
  type RentalDurationMonths,
} from "../../src/marketplace/catalog";
import { ProductAsset } from "../../src/marketplace/assets";
import { useMarketplaceStore } from "../../src/stores/marketplaceStore";
import { toPersianDigits } from "../../src/i18n/numerals";

const RENTAL_DURATIONS: { months: RentalDurationMonths; label: string }[] = [
  { months: 1, label: "۱ ماه" },
  { months: 3, label: "۳ ماه" },
  { months: 6, label: "۶ ماه" },
  { months: 12, label: "۱۲ ماه" },
];

export default function ProductDetailScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const selectedProductId = useMarketplaceStore((state) => state.selectedProductId);
  const configurations = useMarketplaceStore((state) => state.configurations);
  const setMethod = useMarketplaceStore((state) => state.setMethod);
  const setSubscriptionTier = useMarketplaceStore((state) => state.setSubscriptionTier);
  const setRentalDuration = useMarketplaceStore((state) => state.setRentalDuration);

  const product = getProductById(selectedProductId) ?? getProductById("yara-hub")!;
  const config = configurations[product.id] ?? {
    productId: product.id,
    method: "buy" as AcquisitionMethod,
    subscriptionTier: "monthly" as SubscriptionTier,
    rentalDurationMonths: 1 as RentalDurationMonths,
  };
  const calculatedPrice = defaultPricingProvider.calculatePrice(config);

  const isBuy = config.method === "buy";

  function handleBack() {
    router.back();
  }

  function handleProceedToAuth() {
    // Navigate to existing authentication without creating fake backend order state
    router.push("/(auth)/sign-in");
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      {/* Consistent Header across Marketplace & Product Detail */}
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="بازگشت به فهرست محصولات"
          onPress={handleBack}
          hitSlop={12}
          style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
        >
          <Icon name="chevron" color={colors.text} width={20} height={20} />
          <AppText variant="label" color={colors.textSecondary}>
            بازگشت
          </AppText>
        </Pressable>

        <BrandLockup size="sm" />
      </View>

      <ScrollView
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + spacing.xl }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Product Visual Asset */}
        <ProductAsset assetId={product.assetId} size="lg" style={styles.heroAsset} />

        {/* Product Title & Tag */}
        <View style={styles.titleSection}>
          <View style={styles.tagBadge}>
            <AppText variant="caption" color={colors.primary}>
              {product.tag}
            </AppText>
          </View>
          <AppText variant="headline" style={styles.productName}>
            {product.name}
          </AppText>
          <AppText variant="body" color={colors.textSecondary} style={styles.description}>
            {product.fullDescription}
          </AppText>
        </View>

        {/* Included Items Section */}
        <Card style={styles.sectionCard}>
          <AppText variant="title" style={styles.sectionTitle}>
            اقلام و تجهیزات موجود در بسته
          </AppText>
          <View style={styles.includedList}>
            {product.includedDevices.map((item, idx) => (
              <View key={idx} style={styles.includedItemRow}>
                <View style={styles.itemIconWrap}>
                  <Icon name={item.icon} color={colors.primary} width={22} height={22} />
                </View>
                <View style={styles.itemMeta}>
                  <View style={styles.itemNameRow}>
                    <AppText variant="subtitle" color={colors.text}>
                      {item.name}
                    </AppText>
                    <View style={styles.countBadge}>
                      <AppText variant="caption" color={colors.textSecondary}>
                        {toPersianDigits(item.count)} عدد
                      </AppText>
                    </View>
                  </View>
                  <AppText variant="caption" color={colors.textMuted} style={styles.itemDesc}>
                    {item.description}
                  </AppText>
                </View>
              </View>
            ))}
          </View>
        </Card>

        {/* Key Benefits Section */}
        <Card style={styles.sectionCard}>
          <AppText variant="title" style={styles.sectionTitle}>
            ویژگی‌ها و قابلیت‌های محوری
          </AppText>
          <View style={styles.benefitsList}>
            {product.keyBenefits.map((benefit, idx) => (
              <View key={idx} style={styles.benefitRow}>
                <View style={styles.checkWrap}>
                  <Icon name="check" color={colors.success} width={14} height={14} />
                </View>
                <AppText variant="subtitle" color={colors.text} style={styles.benefitText}>
                  {benefit}
                </AppText>
              </View>
            ))}
          </View>
        </Card>

        {/* ============================================================== */}
        {/* NEW ACQUISITION HIERARCHY: LEVEL 1 (BUY vs RENT)                */}
        {/* ============================================================== */}
        <Card style={styles.sectionCard}>
          <AppText variant="title" style={styles.sectionTitle}>
            روش دریافت دستگاه
          </AppText>
          <AppText variant="caption" color={colors.textMuted} style={styles.configHint}>
            نحوه استفاده از تجهیزات یارا را متناسب با نیاز خانواده انتخاب کنید:
          </AppText>

          {/* Level 1 Primary Options */}
          <View style={styles.primaryOptionsRow}>
            {/* 1. BUY THE DEVICE */}
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="خرید دستگاه"
              accessibilityState={{ selected: isBuy }}
              onPress={() => setMethod(product.id, "buy")}
              style={[
                styles.primaryCard,
                isBuy ? styles.primaryCardSelected : styles.primaryCardUnselected,
              ]}
            >
              <View style={styles.radioRow}>
                <View style={[styles.radioOuter, isBuy && styles.radioOuterSelected]}>
                  {isBuy ? <View style={styles.radioInner} /> : null}
                </View>
                <AppText
                  variant="subtitle"
                  color={isBuy ? colors.primary : colors.text}
                  style={styles.cardHeaderTitle}
                >
                  خرید دستگاه
                </AppText>
              </View>
              <AppText variant="caption" color={isBuy ? colors.primary : colors.textSecondary}>
                مالکیت قطعی دستگاه + اشتراک خدمات
              </AppText>
            </Pressable>

            {/* 2. RENT THE DEVICE */}
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="اجاره دستگاه"
              accessibilityState={{ selected: !isBuy }}
              onPress={() => setMethod(product.id, "rent")}
              style={[
                styles.primaryCard,
                !isBuy ? styles.primaryCardSelected : styles.primaryCardUnselected,
              ]}
            >
              <View style={styles.radioRow}>
                <View style={[styles.radioOuter, !isBuy && styles.radioOuterSelected]}>
                  {!isBuy ? <View style={styles.radioInner} /> : null}
                </View>
                <AppText
                  variant="subtitle"
                  color={!isBuy ? colors.primary : colors.text}
                  style={styles.cardHeaderTitle}
                >
                  اجاره دستگاه
                </AppText>
              </View>
              <AppText variant="caption" color={!isBuy ? colors.primary : colors.textSecondary}>
                استفاده برای مدت مشخص بدون خرید
              </AppText>
            </Pressable>
          </View>

          {/* ============================================================== */}
          {/* LEVEL 2: CONDITIONAL CONTROLS (BUY OR RENT)                     */}
          {/* ============================================================== */}
          {isBuy ? (
            <View style={styles.conditionalContainer}>
              {/* 3 Months Free Subscription Gift Callout */}
              <View style={styles.giftBadgeBox}>
                <AppText variant="label" color={colors.primary}>
                  🎁 ۳ ماه اشتراک رایگان همراه خرید دستگاه
                </AppText>
                <AppText variant="caption" color={colors.textSecondary} style={styles.giftDesc}>
                  با خرید دستگاه، ۳ ماه نخست استفاده از خدمات نرم‌افزاری، تماس‌ها و پشتیبانی یارا رایگان خواهد بود.
                </AppText>
              </View>

              <AppText variant="label" style={styles.subOptionHeader}>
                نوع اشتراک خدمات پس از دوره رایگان:
              </AppText>

              {/* Subscription Options */}
              <View style={styles.subOptionsRow}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="اشتراک ماهانه"
                  accessibilityState={{ selected: config.subscriptionTier === "monthly" }}
                  onPress={() => setSubscriptionTier(product.id, "monthly")}
                  style={[
                    styles.subCard,
                    config.subscriptionTier === "monthly"
                      ? styles.subCardSelected
                      : styles.subCardUnselected,
                  ]}
                >
                  <AppText
                    variant="label"
                    color={config.subscriptionTier === "monthly" ? colors.primary : colors.text}
                    align="center"
                  >
                    اشتراک ماهانه
                  </AppText>
                  <AppText variant="caption" color={colors.textMuted} align="center">
                    پرداخت دوره‌ای
                  </AppText>
                </Pressable>

                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="اشتراک سالانه"
                  accessibilityState={{ selected: config.subscriptionTier === "annual" }}
                  onPress={() => setSubscriptionTier(product.id, "annual")}
                  style={[
                    styles.subCard,
                    config.subscriptionTier === "annual"
                      ? styles.subCardSelected
                      : styles.subCardUnselected,
                  ]}
                >
                  <AppText
                    variant="label"
                    color={config.subscriptionTier === "annual" ? colors.primary : colors.text}
                    align="center"
                  >
                    اشتراک سالانه
                  </AppText>
                  <AppText variant="caption" color={colors.primary} align="center">
                    با تخفیف ویژه ۲ ماه
                  </AppText>
                </Pressable>
              </View>
            </View>
          ) : (
            <View style={styles.conditionalContainer}>
              <AppText variant="label" style={styles.subOptionHeader}>
                مدت زمان اجاره دستگاه:
              </AppText>

              {/* Rental Duration Chips */}
              <View style={styles.durationChipsRow}>
                {RENTAL_DURATIONS.map((dur) => {
                  const isSelected = config.rentalDurationMonths === dur.months;
                  return (
                    <Pressable
                      key={dur.months}
                      accessibilityRole="button"
                      accessibilityLabel={`اجاره برای ${dur.label}`}
                      accessibilityState={{ selected: isSelected }}
                      onPress={() => setRentalDuration(product.id, dur.months)}
                      style={[
                        styles.durationChip,
                        isSelected ? styles.durationChipSelected : styles.durationChipUnselected,
                      ]}
                    >
                      <AppText
                        variant="label"
                        color={isSelected ? colors.primaryOn : colors.text}
                        align="center"
                      >
                        {dur.label}
                      </AppText>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          )}

          {/* ============================================================== */}
          {/* PRICE SUMMARY (STRICTLY BELOW CONTROLS, NEVER OVERLAPPING)     */}
          {/* ============================================================== */}
          <View style={styles.priceSummaryBox}>
            <View style={styles.priceHeaderRow}>
              <AppText variant="caption" color={colors.textSecondary}>
                خلاصه مبلغ انتخابی:
              </AppText>
              <View style={styles.modeTag}>
                <AppText variant="caption" color={colors.primary}>
                  {calculatedPrice.modeLabel}
                </AppText>
              </View>
            </View>

            {isBuy ? (
              <View style={styles.breakdownList}>
                <View style={styles.breakdownRow}>
                  <AppText variant="body" color={colors.textSecondary}>
                    قیمت دستگاه (مالکیت قطعی):
                  </AppText>
                  <AppText variant="body" color={colors.text}>
                    {calculatedPrice.formattedDevicePrice}
                  </AppText>
                </View>

                <View style={styles.breakdownRow}>
                  <AppText variant="body" color={colors.textSecondary}>
                    نوع اشتراک:
                  </AppText>
                  <AppText variant="body" color={colors.text}>
                    {calculatedPrice.subscriptionTierLabel} ({calculatedPrice.formattedSubscriptionPrice})
                  </AppText>
                </View>

                <View style={styles.breakdownRow}>
                  <AppText variant="body" color={colors.success}>
                    هدیه خرید:
                  </AppText>
                  <AppText variant="body" color={colors.success}>
                    ۳ ماه اشتراک رایگان
                  </AppText>
                </View>

                <View style={styles.summaryDivider} />

                <View style={styles.breakdownRow}>
                  <AppText variant="title" color={colors.text}>
                    پرداخت اولیه:
                  </AppText>
                  <AppText variant="display" color={colors.primary} style={styles.totalPriceText}>
                    {calculatedPrice.formattedInitialPayment}
                  </AppText>
                </View>
              </View>
            ) : (
              <View style={styles.breakdownList}>
                <View style={styles.breakdownRow}>
                  <AppText variant="body" color={colors.textSecondary}>
                    مدت دوره اجاره:
                  </AppText>
                  <AppText variant="body" color={colors.text}>
                    {toPersianDigits(calculatedPrice.rentalDurationMonths ?? 1)} ماه
                  </AppText>
                </View>

                <View style={styles.summaryDivider} />

                <View style={styles.breakdownRow}>
                  <AppText variant="title" color={colors.text}>
                    مبلغ کل اجاره:
                  </AppText>
                  <AppText variant="display" color={colors.primary} style={styles.totalPriceText}>
                    {calculatedPrice.formattedPrice}
                  </AppText>
                </View>
              </View>
            )}

            <AppText variant="caption" color={colors.textMuted} style={styles.billingNote}>
              {calculatedPrice.billingNote}
            </AppText>
          </View>

          {/* Order Notice & Auth Boundary CTA */}
          <View style={styles.orderCtaBox}>
            <AppText variant="caption" color={colors.textMuted} align="center" style={styles.orderNotice}>
              برای نهایی‌سازی سفارش و ثبت مشخصات تحویل، ابتدا وارد حساب کاربری شوید یا حساب جدید بسازید.
            </AppText>
            <Button
              label="ادامه و ثبت سفارش"
              variant="primary"
              onPress={handleProceedToAuth}
              style={styles.ctaButton}
            />
          </View>
        </Card>

        {/* Medical / Boundary Disclaimer */}
        <View style={styles.disclaimerBox}>
          <Icon name="info" color={colors.textMuted} width={18} height={18} />
          <AppText variant="caption" color={colors.textMuted} style={styles.disclaimerText}>
            تجهیزات و بسته‌های همراهی یارا برای آسایش و تسهیل مراقبت خانوادگی طراحی شده‌اند و جایگزین خدمات اورژانس، پزشک معالج یا تجهیزات مراقبت ویژه بیمارستانی نیستند.
          </AppText>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.screen,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
    minHeight: sizes.touch,
  },
  backButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    minHeight: sizes.touch,
    paddingHorizontal: spacing.xs,
  },
  pressed: {
    opacity: 0.65,
  },
  scrollContent: {
    paddingHorizontal: spacing.screen,
    paddingTop: spacing.sm,
  },
  heroAsset: {
    marginBottom: spacing.lg,
  },
  titleSection: {
    marginBottom: spacing.lg,
  },
  tagBadge: {
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
    alignSelf: "flex-start",
    marginBottom: spacing.xs,
  },
  productName: {
    marginBottom: spacing.xs,
    lineHeight: 34,
  },
  description: {
    lineHeight: 24,
  },
  sectionCard: {
    borderRadius: radius.xl,
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
    marginBottom: spacing.lg,
    ...elevation.card,
  },
  sectionTitle: {
    marginBottom: spacing.xs,
    lineHeight: 28,
  },
  includedList: {
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  includedItemRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.md,
    paddingBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.surfaceMuted,
  },
  itemIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surfaceMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  itemMeta: {
    flex: 1,
  },
  itemNameRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  countBadge: {
    backgroundColor: colors.surfaceSoft,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  itemDesc: {
    marginTop: 2,
    lineHeight: 18,
  },
  benefitsList: {
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  benefitRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  checkWrap: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.successSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  benefitText: {
    flex: 1,
    lineHeight: 22,
  },
  configHint: {
    marginBottom: spacing.md,
    lineHeight: 20,
  },
  primaryOptionsRow: {
    flexDirection: "row",
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  primaryCard: {
    flex: 1,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 2,
    gap: spacing.xs,
  },
  primaryCardSelected: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.primary,
  },
  primaryCardUnselected: {
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
  },
  radioRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  radioOuter: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: colors.borderMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  radioOuterSelected: {
    borderColor: colors.primary,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.primary,
  },
  cardHeaderTitle: {
    lineHeight: 22,
  },
  conditionalContainer: {
    marginVertical: spacing.sm,
    gap: spacing.sm,
  },
  giftBadgeBox: {
    backgroundColor: colors.successSoft,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.successOn + "33",
    gap: 4,
  },
  giftDesc: {
    lineHeight: 18,
  },
  subOptionHeader: {
    marginTop: spacing.xs,
  },
  subOptionsRow: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  subCard: {
    flex: 1,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1.5,
    minHeight: sizes.touch,
    justifyContent: "center",
    alignItems: "center",
    gap: 2,
  },
  subCardSelected: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.primary,
  },
  subCardUnselected: {
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
  },
  durationChipsRow: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  durationChip: {
    flex: 1,
    minHeight: sizes.touch,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.sm,
  },
  durationChipSelected: {
    backgroundColor: colors.primary,
  },
  durationChipUnselected: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  priceSummaryBox: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.lg,
    padding: spacing.md,
    marginVertical: spacing.md,
    gap: spacing.sm,
  },
  priceHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  modeTag: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  breakdownList: {
    gap: spacing.xs,
    marginVertical: spacing.xs,
  },
  breakdownRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  summaryDivider: {
    height: 1,
    backgroundColor: colors.borderMuted,
    marginVertical: spacing.xs,
  },
  totalPriceText: {
    fontSize: 22,
    lineHeight: 32,
  },
  billingNote: {
    lineHeight: 18,
    marginTop: spacing.xs,
  },
  orderCtaBox: {
    marginTop: spacing.sm,
    gap: spacing.sm,
  },
  orderNotice: {
    lineHeight: 20,
  },
  ctaButton: {
    minHeight: sizes.touch + 4,
  },
  disclaimerBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    backgroundColor: colors.surfaceMuted,
    padding: spacing.md,
    borderRadius: radius.md,
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  disclaimerText: {
    flex: 1,
    lineHeight: 18,
  },
});
