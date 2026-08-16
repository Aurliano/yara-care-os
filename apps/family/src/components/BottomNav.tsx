import { Pressable, StyleSheet, View } from "react-native";
import { usePathname, useRouter } from "expo-router";
import { colors, elevation, radius, sizes, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { Icon } from "./Icon";
import type { IconKey } from "../ui/iconXml";
import { t } from "../i18n";

const TABS: { href: string; label: string; icon: IconKey; match: string }[] = [
  { href: "/(app)/(tabs)", label: t.navHome, icon: "nav_home", match: "/(app)/(tabs)" },
  { href: "/(app)/(tabs)/program", label: t.navProgram, icon: "nav_program", match: "program" },
  { href: "/(app)/(tabs)/alerts", label: t.navAlerts, icon: "nav_alerts", match: "alerts" },
  { href: "/(app)/(tabs)/devices", label: t.navDevices, icon: "nav_devices", match: "devices" },
  { href: "/(app)/(tabs)/more", label: t.navMore, icon: "nav_more", match: "more" },
];

export function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <View style={styles.bar}>
      {TABS.map((tab) => {
        const active =
          tab.match === "/(app)/(tabs)"
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
