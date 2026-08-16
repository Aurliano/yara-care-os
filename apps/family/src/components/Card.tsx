import { type ReactNode } from "react";
import { StyleSheet, View, type ViewStyle } from "react-native";
import { colors, elevation, radius, spacing } from "../theme/tokens";

type Props = {
  children: ReactNode;
  style?: ViewStyle;
  accent?: "none" | "success" | "warning" | "error" | "info" | "medication";
};

export function Card({ children, style, accent = "none" }: Props) {
  return (
    <View style={[styles.card, ACCENT[accent], style]}>
      {accent !== "none" ? <View style={[styles.stripe, { backgroundColor: STRIPE[accent] }]} /> : null}
      {children}
    </View>
  );
}

const STRIPE = {
  none: "transparent",
  success: colors.success,
  warning: colors.warningBrown,
  error: colors.error,
  info: colors.info,
  medication: colors.medicationAccent,
} as const;

const ACCENT = {
  none: {},
  success: { borderColor: colors.borderStrong },
  warning: { borderColor: "#FFB59A" },
  error: { borderColor: colors.errorSoft },
  info: { borderColor: colors.borderStrong },
  medication: { borderColor: "rgba(188,201,198,0.3)" },
} as const;

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    padding: spacing.md,
    overflow: "hidden",
    ...elevation.card,
  },
  stripe: {
    position: "absolute",
    top: 0,
    bottom: 0,
    right: 0,
    width: 4,
  },
});
