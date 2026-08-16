import { useState } from "react";
import { Pressable, StyleSheet, Switch, View } from "react-native";
import { useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { AppText, Button, Card, Screen, TextField, TopAppBar } from "../../src/components";
import { Avatar } from "../../src/components/Avatar";
import { Icon } from "../../src/components/Icon";
import { t } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import { useSessionStore } from "../../src/stores/sessionStore";
import { updateCurrentUser } from "../../src/api/endpoints/identity";
import { useElderStore } from "../../src/stores/elderStore";
import { useQueryClient } from "@tanstack/react-query";

export default function SettingsScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useSessionStore((s) => s.user);
  const setUser = useSessionStore((s) => s.setUser);
  const signOut = useSessionStore((s) => s.signOut);
  const clearElder = useElderStore((s) => s.clearElder);
  const [name, setName] = useState(user?.full_name ?? "");
  const save = useMutation({
    mutationFn: () => updateCurrentUser({ full_name: name }),
    onSuccess: (next) => setUser(next),
  });

  return (
    <Screen>
      <TopAppBar title={t.settings} showBack />
      <Card>
        <View style={styles.profile}>
          <Avatar name={user?.full_name ?? "?"} />
          <View style={{ flex: 1 }}>
            <AppText variant="title">{t.account}</AppText>
            <AppText variant="body" color={colors.textSecondary}>
              {t.accountHint}
            </AppText>
          </View>
        </View>
        <TextField label={t.fullName} value={name} onChangeText={setName} persianValue={false} />
        <Button label={t.editProfile} onPress={() => save.mutate()} loading={save.isPending} />
      </Card>

      <AppText variant="label" color={colors.primary}>
        {t.notifications}
      </AppText>
      <Card>
        <View style={styles.row}>
          <Switch value={false} disabled />
          <View style={{ flex: 1 }}>
            <AppText variant="body">دریافت هشدارهای حیاتی</AppText>
            <AppText variant="caption" color={colors.textMuted}>
              {t.notificationPrefsDisabled}
            </AppText>
          </View>
        </View>
      </Card>

      <AppText variant="label" color={colors.primary}>
        {t.privacy}
      </AppText>
      <Card>
        <AppText variant="body">مجوزهای دسترسی</AppText>
        <AppText variant="caption" color={colors.textMuted}>
          {t.privacyDisabled}
        </AppText>
      </Card>

      <AppText variant="label" color={colors.primary}>
        {t.about}
      </AppText>
      <Card>
        <View style={styles.row}>
          <AppText variant="caption">v 0.1.0</AppText>
          <AppText variant="body">{t.version}</AppText>
        </View>
      </Card>

      <Pressable
        onPress={async () => {
          await clearElder();
          await signOut();
          queryClient.clear();
          router.replace("/(auth)/sign-in");
        }}
        style={styles.logout}
      >
        <AppText variant="bodyStrong" color={colors.error} align="center">
          {t.logout}
        </AppText>
        <Icon name="logout" color={colors.error} width={18} height={18} />
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  profile: { flexDirection: "row", gap: spacing.md, alignItems: "center", marginBottom: spacing.md },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.md },
  logout: {
    marginTop: spacing.lg,
    backgroundColor: "rgba(255,218,214,0.3)",
    borderColor: "rgba(186,26,26,0.2)",
    borderWidth: 1,
    borderRadius: 12,
    minHeight: 44,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    padding: spacing.md,
  },
});
