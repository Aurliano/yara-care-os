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
import { PRODUCTS, formatToman, type MarketplaceProduct } from "../../src/marketplace/catalog";
import { ProductAsset } from "../../src/marketplace/assets";
import { useMarketplaceStore } from "../../src/stores/marketplaceStore";

export default function MarketplaceScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const setSelectedProductId = useMarketplaceStore((state) => state.setSelectedProductId);

  function handleOpenProduct(product: MarketplaceProduct) {
    setSelectedProductId(product.id);
    router.push("/(auth)/product-detail");
  }

  function handleBack() {
    if (router.canGoBack()) {
      router.back();
    } else {
      router.replace("/(auth)/discovery");
    }
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      {/* Top Header Bar */}
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="بازگشت"
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

      {/* Main Content */}
      <ScrollView
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + spacing.xl }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero Section */}
        <View style={styles.titleSection}>
          <AppText variant="headline" style={styles.headline}>
            بسته‌ها و تجهیزات یارا
          </AppText>
          <AppText variant="body" color={colors.textSecondary} style={styles.subhead}>
            تجهیزات آرامش‌بخش خانه و زیست‌بوم مراقبت سالمند؛ متناسب با شرایط و نیاز خانواده عزیزتان انتخاب کنید.
          </AppText>
        </View>

        {/* Product Cards */}
        <View style={styles.productList}>
          {PRODUCTS.map((product) => (
            <Card key={product.id} style={styles.productCard}>
              {/* Product Asset Illustration */}
              <ProductAsset assetId={product.assetId} size="md" />

              {/* Tag and Title */}
              <View style={styles.cardHeader}>
                <View style={styles.tagBadge}>
                  <AppText variant="caption" color={colors.primary}>
                    {product.tag}
                  </AppText>
                </View>
                <AppText variant="title" style={styles.productTitle}>
                  {product.name}
                </AppText>
              </View>

              {/* Description */}
              <AppText variant="body" color={colors.textSecondary} style={styles.productDesc}>
                {product.shortDescription}
              </AppText>

              {/* Included Devices Chips */}
              <View style={styles.devicesWrap}>
                <AppText variant="caption" color={colors.textMuted} style={styles.devicesLabel}>
                  اقلام همراه:
                </AppText>
                <View style={styles.chipsRow}>
                  {product.includedDevices.map((dev, idx) => (
                    <View key={idx} style={styles.deviceChip}>
                      <Icon name={dev.icon} color={colors.primary} width={14} height={14} />
                      <AppText variant="caption" color={colors.text}>
                        {dev.name}
                      </AppText>
                    </View>
                  ))}
                </View>
              </View>

              {/* Price and CTA Row */}
              <View style={styles.priceCtaRow}>
                <View style={styles.priceContainer}>
                  <AppText variant="caption" color={colors.textMuted}>
                    شروع قیمت از:
                  </AppText>
                  <AppText variant="title" color={colors.primary} style={styles.priceText}>
                    {formatToman(product.startingPrice)}
                  </AppText>
                </View>

                <Button
                  label="مشاهده جزئیات"
                  variant="primary"
                  onPress={() => handleOpenProduct(product)}
                  style={styles.detailButton}
                />
              </View>
            </Card>
          ))}
        </View>

        {/* Footer Link to Sign In */}
        <View style={styles.footerSection}>
          <AppText variant="caption" color={colors.textMuted} align="center">
            قبلاً حساب کاربری ساخته‌اید یا اشتراک دارید؟
          </AppText>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="ورود به حساب کاربری"
            onPress={() => router.replace("/(auth)/sign-in")}
            hitSlop={10}
            style={({ pressed }) => [styles.signInLink, pressed && styles.pressed]}
          >
            <AppText variant="label" color={colors.primary} align="center">
              ورود به حساب کاربری
            </AppText>
          </Pressable>
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
    minWidth: sizes.touch,
    paddingHorizontal: spacing.xs,
  },
  pressed: {
    opacity: 0.65,
  },
  scrollContent: {
    paddingHorizontal: spacing.screen,
    paddingTop: spacing.sm,
  },
  titleSection: {
    marginBottom: spacing.lg,
  },
  headline: {
    marginBottom: spacing.xs,
    lineHeight: 34,
  },
  subhead: {
    lineHeight: 24,
  },
  productList: {
    gap: spacing.lg,
  },
  productCard: {
    borderRadius: radius.xl,
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
    ...elevation.card,
  },
  cardHeader: {
    marginTop: spacing.md,
    marginBottom: spacing.xs,
    alignItems: "flex-start",
  },
  tagBadge: {
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
    marginBottom: spacing.xs,
  },
  productTitle: {
    lineHeight: 28,
  },
  productDesc: {
    lineHeight: 22,
    marginBottom: spacing.md,
  },
  devicesWrap: {
    backgroundColor: colors.surfaceMuted,
    padding: spacing.md,
    borderRadius: radius.md,
    marginBottom: spacing.lg,
    gap: spacing.xs,
  },
  devicesLabel: {
    marginBottom: spacing.xs,
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  deviceChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  priceCtaRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.md,
    gap: spacing.md,
  },
  priceContainer: {
    flex: 1,
  },
  priceText: {
    fontSize: 18,
    lineHeight: 24,
  },
  detailButton: {
    flexShrink: 0,
    minWidth: 120,
  },
  footerSection: {
    marginTop: spacing.xl,
    alignItems: "center",
    gap: spacing.xs,
  },
  signInLink: {
    minHeight: sizes.touch,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
});
