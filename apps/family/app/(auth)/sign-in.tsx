import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Link, useRouter } from "expo-router";
import { t } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import { AppText, Button, Card, Screen, TextField } from "../../src/components";
import { useSessionStore } from "../../src/stores/sessionStore";
import { ApiError } from "../../src/api/errors";

export default function SignInScreen() {
  const router = useRouter();
  const signIn = useSessionStore((state) => state.signIn);
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit() {
    setError(null);
    setLoading(true);
    try {
      await signIn(phone, password);
      router.replace("/(auth)/select-elder");
    } catch (err) {
      setError(err instanceof ApiError ? "ورود ناموفق بود. شماره یا رمز را بررسی کنید." : t.errorBody);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <View style={styles.brand}>
        <AppText variant="headline" color={colors.primary} align="center">
          {t.brand}
        </AppText>
        <AppText variant="title" align="center">
          {t.tagline}
        </AppText>
        <AppText variant="body" color={colors.textSecondary} align="center">
          {t.signInHint}
        </AppText>
      </View>
      <Card>
        <View style={styles.form}>
          <TextField
            label={t.phone}
            value={phone}
            onChangeText={setPhone}
            placeholder="۰۹۱۲۳۴۵۶۷۸۹"
            icon="phone"
            keyboardType="phone-pad"
          />
          <TextField
            label={t.password}
            value={password}
            onChangeText={setPassword}
            placeholder="••••••••"
            icon="lock"
            secure
            persianValue={false}
          />
          {error ? (
            <AppText variant="caption" color={colors.error} align="center">
              {error}
            </AppText>
          ) : null}
          <Button label={t.signIn} onPress={() => void onSubmit()} loading={loading} />
          <Button
            label={t.createAccount}
            variant="secondary"
            onPress={() => router.push("/(auth)/register")}
          />
        </View>
      </Card>
      <View style={styles.footer}>
        <AppText variant="caption" color={colors.textMuted}>
          {t.contactSupport}
        </AppText>
        <AppText variant="caption" color={colors.primary}>
          {`${t.forgotPassword} — ${t.unavailableFeature}`}
        </AppText>
      </View>
      <Link href="/(auth)/accept-invitation" style={styles.link}>
        <AppText variant="label" color={colors.primary} align="center">
          {t.acceptInvite}
        </AppText>
      </Link>
    </Screen>
  );
}

const styles = StyleSheet.create({
  brand: { gap: spacing.sm, alignItems: "center", marginBottom: spacing.lg, marginTop: spacing.xl },
  form: { gap: spacing.md, width: "100%" },
  footer: { marginTop: spacing.lg, flexDirection: "row", justifyContent: "space-between" },
  link: { marginTop: spacing.lg, alignSelf: "center" },
});
