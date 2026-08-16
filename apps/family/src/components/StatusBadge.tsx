import { StyleSheet, View } from "react-native";
import { colors, radius, spacing } from "../theme/tokens";
import { AppText } from "./AppText";

type Tone = "success" | "warning" | "error" | "neutral" | "info";

const TONE = {
  success: { bg: colors.successSoft, fg: colors.primary, dot: colors.primary },
  warning: { bg: colors.warningSoft, fg: colors.warningBrown, dot: colors.warningAccent },
  error: { bg: colors.errorSoft, fg: colors.errorOn, dot: colors.error },
  neutral: { bg: colors.surfaceMuted, fg: colors.textSecondary, dot: colors.textMuted },
  info: { bg: colors.infoSoft, fg: colors.infoOn, dot: colors.info },
} as const;

export function StatusBadge({ label, tone = "neutral" }: { label: string; tone?: Tone }) {
  const palette = TONE[tone];
  return (
    <View style={[styles.badge, { backgroundColor: palette.bg }]}>
      <AppText variant="caption" color={palette.fg}>
        {label}
      </AppText>
      <View style={[styles.dot, { backgroundColor: palette.dot }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: radius.pill,
  },
  dot: { width: 8, height: 8, borderRadius: radius.pill },
});
