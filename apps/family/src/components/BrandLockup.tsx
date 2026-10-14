import { Image, StyleSheet, View } from "react-native";
import { t } from "../i18n";
import { spacing } from "../theme/tokens";
import { images } from "./Icon";

type Size = "sm" | "md" | "lg";

const SIZES: Record<Size, { emblemW: number; emblemH: number; wordmarkW: number; wordmarkH: number }> = {
  sm: { emblemW: 34, emblemH: 28, wordmarkW: 98, wordmarkH: 18 },
  md: { emblemW: 46, emblemH: 38, wordmarkW: 130, wordmarkH: 24 },
  lg: { emblemW: 70, emblemH: 58, wordmarkW: 196, wordmarkH: 36 },
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
