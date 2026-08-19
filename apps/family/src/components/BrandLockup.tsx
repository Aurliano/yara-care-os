import { Image, StyleSheet, View } from "react-native";
import { t } from "../i18n";
import { spacing } from "../theme/tokens";
import { images } from "./Icon";

type Size = "sm" | "md" | "lg";

const SIZES: Record<Size, { emblemW: number; emblemH: number; wordmarkW: number; wordmarkH: number }> = {
  sm: { emblemW: 30, emblemH: 32, wordmarkW: 90, wordmarkH: 22 },
  md: { emblemW: 40, emblemH: 43, wordmarkW: 120, wordmarkH: 29 },
  lg: { emblemW: 56, emblemH: 60, wordmarkW: 168, wordmarkH: 41 },
};

type Props = {
  size?: Size;
};

export function BrandLockup({ size = "sm" }: Props) {
  const dims = SIZES[size];
  return (
    <View
      accessibilityRole="image"
      accessibilityLabel={t.brand}
      style={styles.row}
    >
      <Image
        source={images.logo}
        style={{ width: dims.emblemW, height: dims.emblemH }}
        resizeMode="contain"
      />
      <Image
        source={images.wordmark}
        style={{ width: dims.wordmarkW, height: dims.wordmarkH }}
        resizeMode="contain"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    direction: "ltr",
  },
});
