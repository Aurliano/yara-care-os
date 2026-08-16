import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { t } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import { AppText, Button, Card, Screen, TextField, TopAppBar } from "../../src/components";
import { registerUser } from "../../src/api/endpoints/identity";
import { useSessionStore } from "../../src/stores/sessionStore";
import { toLatinDigits } from "../../src/i18n/numerals";

export default function RegisterScreen() {
  const router = useRouter();
  const signIn = useSessionStore((state) => state.signIn);
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit() {
    setLoading(true);
    setError(null);
    try {
      await registerUser({
        phone: toLatinDigits(phone).trim(),
        password,
        full_name: fullName.trim(),
      });
      await signIn(phone, password);
      router.replace("/(auth)/select-elder");
    } catch {
      setError("ایجاد حساب انجام نشد. اگر این شماره قبلاً ثبت شده، وارد شوید.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <TopAppBar title={t.createAccount} showBell={false} showBack />
      <Card>
        <View style={styles.form}>
          <TextField label={t.fullName} value={fullName} onChangeText={setFullName} persianValue={false} />
          <TextField
            label={t.phone}
            value={phone}
            onChangeText={setPhone}
            icon="phone"
            keyboardType="phone-pad"
          />
          <TextField
            label={t.password}
            value={password}
            onChangeText={setPassword}
            icon="lock"
            secure
            persianValue={false}
          />
          {error ? (
            <AppText variant="caption" color={colors.error}>
              {error}
            </AppText>
          ) : null}
          <Button label={t.createAccount} onPress={() => void onSubmit()} loading={loading} />
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  form: { gap: spacing.md },
});
