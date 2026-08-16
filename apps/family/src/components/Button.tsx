import { ActivityIndicator, Pressable, StyleSheet, type ViewStyle } from "react-native";
import { colors, radius, sizes } from "../theme/tokens";
import { AppText } from "./AppText";
import { Icon } from "./Icon";
import type { IconKey } from "../ui/iconXml";

type Variant = "primary" | "secondary" | "danger" | "ghost";

type Props = {
  label: string;
  onPress?: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: Variant;
  icon?: IconKey;
  style?: ViewStyle;
};

export function Button({
  label,
  onPress,
  disabled,
  loading,
  variant = "primary",
  icon,
  style,
}: Props) {
  const palette = PALETTE[variant];
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.base,
        { backgroundColor: palette.bg, borderColor: palette.border, borderWidth: palette.borderWidth },
        (disabled || loading) && styles.disabled,
        pressed && !disabled && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={palette.fg} />
      ) : (
        <>
          <AppText variant="label" color={palette.fg} align="center">
            {label}
          </AppText>
          {icon ? <Icon name={icon} color={palette.fg} width={16} height={16} /> : null}
        </>
      )}
    </Pressable>
  );
}

const PALETTE = {
  primary: { bg: colors.primary, fg: colors.primaryOn, border: colors.primary, borderWidth: 0 },
  secondary: { bg: colors.surface, fg: colors.secondary, border: colors.secondary, borderWidth: 2 },
  danger: { bg: "transparent", fg: colors.error, border: colors.error, borderWidth: 1 },
  ghost: { bg: "transparent", fg: colors.primary, border: "transparent", borderWidth: 0 },
} as const;

const styles = StyleSheet.create({
  base: {
    minHeight: sizes.touch,
    borderRadius: radius.pill,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.85 },
});
