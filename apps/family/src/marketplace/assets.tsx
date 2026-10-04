import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Image,
  type ImageResizeMode,
  type ImageSourcePropType,
  StyleSheet,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import { colors, radius, spacing } from "../theme/tokens";
import { Icon } from "../components/Icon";
import { AppText } from "../components/AppText";
import type { IconKey } from "../ui/iconXml";

export type SemanticProductAssetId =
  | "yara-hub-hero"
  | "yara-hub-lifestyle"
  | "yara-hub-ui"
  | "smart-pillbox-hero"
  | "smart-pillbox-lifestyle"
  | "yara-wearable-hero"
  | "yara-wearable-lifestyle"
  | "yara-care-bundle"
  | "yara-care-plus-bundle"
  | "yara-hub-pillbox-ecosystem"
  | "yara-full-ecosystem"
  | "yara-marketplace-hero";

export type LegacyProductAssetId =
  | "yara-hub"
  | "yara-care"
  | "yara-care-plus"
  | "smart-pillbox"
  | "wearable";

export type ProductAssetId = SemanticProductAssetId | LegacyProductAssetId;

export interface ProductAssetProps {
  assetId: ProductAssetId;
  size?: "sm" | "md" | "lg" | "hero";
  resizeMode?: ImageResizeMode;
  style?: StyleProp<ViewStyle>;
  showCaption?: boolean;
}

export const PRODUCT_IMAGE_SOURCES: Record<SemanticProductAssetId, ImageSourcePropType> = {
  "yara-hub-hero": require("../../assets/images/yara-hub-hero.png"),
  "yara-hub-lifestyle": require("../../assets/images/yara-hub-lifestyle.png"),
  "yara-hub-ui": require("../../assets/images/yara-hub-ui.jpg"),
  "smart-pillbox-hero": require("../../assets/images/smart-pillbox-hero.jpg"),
  "smart-pillbox-lifestyle": require("../../assets/images/smart-pillbox-lifestyle.jpg"),
  "yara-wearable-hero": require("../../assets/images/yara-wearable-hero.jpg"),
  "yara-wearable-lifestyle": require("../../assets/images/yara-wearable-lifestyle.jpg"),
  "yara-care-bundle": require("../../assets/images/yara-care-bundle.jpg"),
  "yara-care-plus-bundle": require("../../assets/images/yara-care-plus-bundle.jpg"),
  "yara-hub-pillbox-ecosystem": require("../../assets/images/yara-hub-pillbox-ecosystem.jpg"),
  "yara-full-ecosystem": require("../../assets/images/yara-full-ecosystem.jpg"),
  "yara-marketplace-hero": require("../../assets/images/yara-marketplace-hero.jpg"),
};

export function resolveSemanticAssetId(assetId: ProductAssetId): SemanticProductAssetId {
  switch (assetId) {
    case "yara-hub":
      return "yara-hub-hero";
    case "yara-care":
      return "yara-care-bundle";
    case "yara-care-plus":
      return "yara-care-plus-bundle";
    case "smart-pillbox":
      return "smart-pillbox-hero";
    case "wearable":
      return "yara-wearable-hero";
    default:
      return assetId;
  }
}

interface AssetMetadata {
  label: string;
  accentColor: string;
  primaryIcon: IconKey;
  secondaryIcons?: IconKey[];
  defaultResizeMode: ImageResizeMode;
  bgColor: string;
}

const ASSET_META: Record<SemanticProductAssetId, AssetMetadata> = {
  "yara-hub-hero": {
    label: "هاب یارا",
    accentColor: colors.primary,
    primaryIcon: "hub",
    defaultResizeMode: "contain",
    bgColor: "#EBE5DB",
  },
  "yara-hub-lifestyle": {
    label: "هاب در خانه",
    accentColor: colors.primary,
    primaryIcon: "hub",
    defaultResizeMode: "cover",
    bgColor: "#EAE7DF",
  },
  "yara-hub-ui": {
    label: "نمایشگر هاب یارا",
    accentColor: colors.primary,
    primaryIcon: "hub",
    defaultResizeMode: "contain",
    bgColor: "#EAE5DC",
  },
  "smart-pillbox-hero": {
    label: "جعبه داروی هوشمند",
    accentColor: colors.primary,
    primaryIcon: "pillbox",
    defaultResizeMode: "contain",
    bgColor: "#E4DACD",
  },
  "smart-pillbox-lifestyle": {
    label: "جعبه دارو در خانه",
    accentColor: colors.primary,
    primaryIcon: "pillbox",
    defaultResizeMode: "cover",
    bgColor: "#EAE7DF",
  },
  "yara-wearable-hero": {
    label: "دستبند سلامت یارا",
    accentColor: colors.secondary,
    primaryIcon: "walking",
    defaultResizeMode: "contain",
    bgColor: "#EFEBE5",
  },
  "yara-wearable-lifestyle": {
    label: "همراهی دستبند سلامت",
    accentColor: colors.secondary,
    primaryIcon: "walking",
    defaultResizeMode: "cover",
    bgColor: "#EAE7DF",
  },
  "yara-care-bundle": {
    label: "بسته مراقبت یارا",
    accentColor: colors.primary,
    primaryIcon: "hub",
    secondaryIcons: ["pillbox"],
    defaultResizeMode: "contain",
    bgColor: "#E6DCCE",
  },
  "yara-care-plus-bundle": {
    label: "بسته مراقبت پلاس یارا",
    accentColor: colors.secondary,
    primaryIcon: "hub",
    secondaryIcons: ["pillbox", "walking"],
    defaultResizeMode: "contain",
    bgColor: "#E6DCCE",
  },
  "yara-hub-pillbox-ecosystem": {
    label: "پیوند هاب و جعبه دارو",
    accentColor: colors.primary,
    primaryIcon: "hub",
    secondaryIcons: ["pillbox"],
    defaultResizeMode: "cover",
    bgColor: "#EAE7DF",
  },
  "yara-full-ecosystem": {
    label: "اکوسیستم کامل یارا",
    accentColor: colors.secondary,
    primaryIcon: "hub",
    secondaryIcons: ["pillbox", "walking"],
    defaultResizeMode: "cover",
    bgColor: "#EAE7DF",
  },
  "yara-marketplace-hero": {
    label: "زیست‌بوم مراقبت سالمند یارا",
    accentColor: colors.primary,
    primaryIcon: "hub",
    secondaryIcons: ["pillbox", "walking"],
    defaultResizeMode: "cover",
    bgColor: "#EAE7DF",
  },
};

const SIZES = {
  sm: { containerH: 80, iconSize: 24, secSize: 16 },
  md: { containerH: 200, iconSize: 36, secSize: 20 },
  lg: { containerH: 260, iconSize: 52, secSize: 26 },
  hero: { containerH: 210, iconSize: 52, secSize: 26 },
};

/**
 * ProductAsset Component
 *
 * Renders high-fidelity studio/lifestyle photography of the Yara Hardware Ecosystem
 * with smooth lazy loading, subtle loading placeholders, proper aspect containment,
 * and a robust icon fallback mechanism.
 */
export function ProductAsset({
  assetId,
  size = "md",
  resizeMode,
  style,
  showCaption = false,
}: ProductAssetProps) {
  const semanticId = resolveSemanticAssetId(assetId);
  const meta = ASSET_META[semanticId];
  const dims = SIZES[size];
  const imageSource = PRODUCT_IMAGE_SOURCES[semanticId];
  const effectiveResizeMode = resizeMode ?? meta.defaultResizeMode;

  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  
  const hasAnimated = typeof Animated !== "undefined" && typeof Animated?.Value === "function";
  const fadeAnim = useRef(hasAnimated ? new Animated.Value(0) : null).current;
  const pulseAnim = useRef(hasAnimated ? new Animated.Value(0.4) : null).current;

  // Gentle breathing shimmer effect while image loads
  useEffect(() => {
    if (!isLoaded && !hasError && pulseAnim && hasAnimated) {
      const pulseLoop = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 0.85,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 0.4,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      );
      pulseLoop.start();
      return () => pulseLoop.stop();
    }
  }, [isLoaded, hasError, pulseAnim, hasAnimated]);

  const handleLoad = () => {
    setIsLoaded(true);
    if (fadeAnim && hasAnimated) {
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
  };

  const handleError = () => {
    setHasError(true);
    setIsLoaded(true);
  };

  const ImageComponent: any = hasAnimated && Animated?.Image ? Animated.Image : Image;
  const PlaceholderContainer: any = hasAnimated && Animated?.View ? Animated.View : View;

  return (
    <View
      style={[
        styles.container,
        { minHeight: dims.containerH, backgroundColor: meta.bgColor },
        size === "lg" && styles.containerLg,
        size === "hero" && styles.containerHero,
        style,
      ]}
      accessibilityRole="image"
      accessibilityLabel={`تصویر ${meta.label}`}
    >
      {/* Loading Shimmer Placeholder */}
      {!isLoaded && !hasError && (
        <PlaceholderContainer
          style={[
            StyleSheet.absoluteFillObject,
            styles.placeholderWrap,
            hasAnimated && pulseAnim ? { opacity: pulseAnim } : { opacity: 0.6 },
          ]}
        >
          <View style={styles.spinnerBadge}>
            <ActivityIndicator size="small" color={meta.accentColor} />
          </View>
        </PlaceholderContainer>
      )}

      {/* Main Photographic Asset */}
      {!hasError && imageSource && (
        <ImageComponent
          source={imageSource}
          resizeMode={effectiveResizeMode}
          fadeDuration={300}
          onLoad={handleLoad}
          onError={handleError}
          style={[
            styles.imageStyle,
            hasAnimated && fadeAnim ? { opacity: fadeAnim } : null,
            effectiveResizeMode === "contain" && styles.imageContainPadding,
          ]}
        />
      )}

      {/* Fallback Icon Badge Cluster if image errors */}
      {hasError && (
        <View style={styles.fallbackContainer}>
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
          <AppText variant="caption" color={colors.textMuted} align="center">
            {meta.label}
          </AppText>
        </View>
      )}

      {/* Optional Caption Overlay */}
      {showCaption && (
        <View style={styles.captionBadge}>
          <AppText variant="caption" color={colors.textSecondary} align="center">
            {meta.label}
          </AppText>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    borderRadius: radius.lg,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    position: "relative",
  },
  containerLg: {
    borderRadius: radius.xl,
  },
  containerHero: {
    borderRadius: radius.xl,
    aspectRatio: 16 / 9,
    maxHeight: 230,
  },
  imageStyle: {
    width: "100%",
    height: "100%",
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  imageContainPadding: {
    padding: spacing.xs,
  },
  placeholderWrap: {
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "transparent",
  },
  spinnerBadge: {
    backgroundColor: colors.surface,
    padding: spacing.sm,
    borderRadius: radius.pill,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  fallbackContainer: {
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.md,
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
    position: "absolute",
    bottom: spacing.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
    backgroundColor: "rgba(255, 255, 255, 0.85)",
  },
});
