import { Pressable, StyleSheet, View } from "react-native";
import { usePathname, useRouter } from "expo-router";
import { colors, elevation, radius, sizes, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { Icon } from "./Icon";
import { APP_TABS } from "../navigation/tabs";

export function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <View style={styles.bar}>
      {APP_TABS.map((tab) => {
        const active =
          tab.match === "home"
            ? pathname === "/" || pathname.endsWith("/(tabs)") || pathname === "/(app)/(tabs)"
            : pathname.includes(tab.match);
        return (
          <Pressable
            key={tab.href}
            accessibilityRole="tab"
            accessibilityState={{ selected: active }}
            accessibilityLabel={tab.label}
            onPress={() => router.replace(tab.href as never)}
            style={styles.item}
          >
            <Icon
              name={tab.icon}
              color={active ? colors.primary : colors.textSecondary}
              width={tab.icon === "nav_more" ? 16 : 18}
              height={tab.icon === "nav_more" ? 8 : 20}
            />
            <AppText
              variant="caption"
              color={active ? colors.primary : colors.textSecondary}
              align="center"
            >
              {tab.label}
            </AppText>
            {active ? <View style={styles.dot} /> : <View style={styles.dotSpacer} />}
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    height: sizes.nav,
    backgroundColor: colors.background,
    borderTopWidth: 1,
    borderTopColor: colors.borderStrong,
    borderTopLeftRadius: radius.md,
    borderTopRightRadius: radius.md,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    paddingBottom: spacing.xs,
    ...elevation.bar,
  },
  item: { flex: 1, alignItems: "center", justifyContent: "center", minHeight: sizes.touch },
  dot: {
    width: 4,
    height: 4,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    marginTop: 2,
  },
  dotSpacer: { width: 4, height: 4, marginTop: 2 },
});
