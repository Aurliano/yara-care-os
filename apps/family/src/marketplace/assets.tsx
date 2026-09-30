import React from "react";
import { StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";
import { colors, radius, spacing } from "../theme/tokens";
import { Icon } from "../components/Icon";
import { AppText } from "../components/AppText";
import type { IconKey } from "../ui/iconXml";

export type ProductAssetId =
  | "yara-hub"
  | "yara-care"
  | "yara-care-plus"
  | "smart-pillbox"
  | "wearable";

export interface ProductAssetProps {
  assetId: ProductAssetId;
  size?: "sm" | "md" | "lg";
  style?: StyleProp<ViewStyle>;
}

const ASSET_META: Record<
  ProductAssetId,
  { primaryIcon: IconKey; secondaryIcons?: IconKey[]; label: string; accentColor: string }
> = {
  "yara-hub": {
    primaryIcon: "hub",
    label: "هاب یارا",
    accentColor: colors.primary,
  },
  "yara-care": {
    primaryIcon: "hub",
    secondaryIcons: ["pillbox"],
    label: "هاب + جعبه دارو",
    accentColor: colors.primary,
  },
  "yara-care-plus": {
    primaryIcon: "hub",
    secondaryIcons: ["pillbox", "walking"],
    label: "هاب + دارو + پوشیدنی",
    accentColor: colors.secondary,
  },
  "smart-pillbox": {
    primaryIcon: "pillbox",
    label: "جعبه دارو",
    accentColor: colors.primary,
  },
  wearable: {
    primaryIcon: "walking",
    label: "پوشیدنی سلامت",
    accentColor: colors.secondary,
  },
};

const SIZES = {
  sm: { containerH: 72, iconSize: 24, secSize: 16 },
  md: { containerH: 120, iconSize: 36, secSize: 20 },
  lg: { containerH: 180, iconSize: 52, secSize: 26 },
};

/**
 * Visual Asset Abstraction for Yara Marketplace.
 *
 * Provides a clean presentation placeholder for Yara hardware and packages.
 * When official product photography is ready, this abstraction allows drop-in
 * replacement with real photographic assets without modifying product cards,
 * detail views, or catalog business logic.
 */
export function ProductAsset({ assetId, size = "md", style }: ProductAssetProps) {
  const meta = ASSET_META[assetId];
  const dims = SIZES[size];

  return (
    <View
      style={[
        styles.container,
        { minHeight: dims.containerH },
        size === "lg" && styles.containerLg,
        style,
      ]}
      accessibilityRole="image"
      accessibilityLabel={`تصویر ${meta.label}`}
    >
      <View style={styles.iconCluster}>
        <View style={[styles.mainIconBadge, { borderColor: meta.accentColor + "33" }]}>
          <Icon name={meta.primaryIcon} color={meta.accentColor} width={dims.iconSize} height={dims.iconSize} />
        </View>
        {meta.secondaryIcons?.map((secIcon, idx) => (
          <View key={idx} style={[styles.secIconBadge, { borderColor: colors.borderMuted }]}>
            <Icon name={secIcon} color={colors.textSecondary} width={dims.secSize} height={dims.secSize} />
          </View>
        ))}
      </View>
      <View style={styles.captionBadge}>
        <AppText variant="caption" color={colors.textMuted} align="center">
          {meta.label}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.lg,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.md,
    overflow: "hidden",
  },
  containerLg: {
    paddingVertical: spacing.lg,
  },
  iconCluster: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    marginBottom: spacing.xs,
  },
  mainIconBadge: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.pill,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  secIconBadge: {
    backgroundColor: colors.surface,
    padding: spacing.sm,
    borderRadius: radius.pill,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  captionBadge: {
    marginTop: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
    backgroundColor: colors.surfaceSoft,
  },
});
