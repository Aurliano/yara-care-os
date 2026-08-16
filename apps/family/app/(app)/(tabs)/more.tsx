import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { t } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import { AppText, Card, Screen, TopAppBar } from "../../../src/components";
import { Icon } from "../../../src/components/Icon";
import { useSessionStore } from "../../../src/stores/sessionStore";
import { useElderStore } from "../../../src/stores/elderStore";
import { useQueryClient } from "@tanstack/react-query";

const LINKS = [
  { href: "/(app)/family", label: t.familyLink, icon: "user_plus" as const },
  { href: "/(app)/subscription", label: t.subscriptionLink, icon: "info" as const },
  { href: "/(app)/settings", label: t.settingsLink, icon: "lock" as const },
];

export default function MoreScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const signOut = useSessionStore((s) => s.signOut);
  const clearElder = useElderStore((s) => s.clearElder);

  return (
    <Screen>
      <TopAppBar title={t.moreTitle} />
      <View style={styles.list}>
        {LINKS.map((link) => (
          <Pressable key={link.href} onPress={() => router.push(link.href as never)}>
            <Card>
              <View style={styles.row}>
                <Icon name="chevron" width={16} height={16} color={colors.textMuted} />
                <AppText variant="body" style={{ flex: 1 }}>
                  {link.label}
                </AppText>
                <Icon name={link.icon} width={18} height={18} />
              </View>
            </Card>
          </Pressable>
        ))}
        <Pressable onPress={() => router.push("/(auth)/select-elder")}>
          <Card>
            <AppText variant="body">{t.switchElder}</AppText>
          </Card>
        </Pressable>
        <Pressable
          onPress={async () => {
            await clearElder();
            await signOut();
            queryClient.clear();
            router.replace("/(auth)/sign-in");
          }}
        >
          <Card>
            <View style={styles.row}>
              <AppText variant="body" color={colors.error} style={{ flex: 1 }}>
                {t.logout}
              </AppText>
              <Icon name="logout" color={colors.error} width={18} height={18} />
            </View>
          </Card>
        </Pressable>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: { gap: spacing.md },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md },
});
