import { type ReactNode } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { colors, sizes, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";
import { Icon } from "./Icon";
import { t } from "../i18n";

type Props = {
  title?: string;
  showBell?: boolean;
  showBack?: boolean;
  trailing?: ReactNode;
};

export function TopAppBar({ title = t.brand, showBell = true, showBack = false, trailing }: Props) {
  const router = useRouter();
  return (
    <View style={styles.bar}>
      {showBack ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t.backHome}
          hitSlop={8}
          onPress={() => router.back()}
          style={styles.hit}
        >
          <Icon name="chevron" width={16} height={16} color={colors.primary} />
        </Pressable>
      ) : showBell ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t.navAlerts}
          hitSlop={8}
          onPress={() => router.push("/(app)/(tabs)/alerts")}
          style={styles.hit}
        >
          <Icon name="bell" width={16} height={20} color={colors.primary} />
        </Pressable>
      ) : (
        <View style={styles.hit} />
      )}
      <AppText variant="headline" color={colors.primary} align="center" style={styles.title}>
        {title}
      </AppText>
      <View style={styles.hit}>{trailing}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    minHeight: 44,
    paddingHorizontal: spacing.screen,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.background,
  },
  title: { flex: 1, ...typography.headline },
  hit: {
    width: sizes.touch,
    height: sizes.touch,
    alignItems: "center",
    justifyContent: "center",
  },
});
