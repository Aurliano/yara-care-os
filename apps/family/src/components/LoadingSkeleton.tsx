import { StyleSheet, View } from "react-native";
import { colors, radius, spacing } from "../theme/tokens";

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <View style={styles.wrap} accessibilityLabel="در حال بارگذاری">
      {Array.from({ length: rows }).map((_, index) => (
        <View key={index} style={styles.block} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.md },
  block: {
    height: 88,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceMuted,
  },
});
