import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { t } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import { AppText, Button, Card, Screen, TextField, TopAppBar } from "../../src/components";
import { registerUser } from "../../src/api/endpoints/identity";
import { useSessionStore } from "../../src/stores/sessionStore";
import { normalizePhone } from "../../src/i18n/numerals";
import { ApiError } from "../../src/api/errors";

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
      const canonicalPhone = normalizePhone(phone);
      await registerUser({
        phone: canonicalPhone,
        password,
        full_name: fullName.trim(),
      });
      await signIn(canonicalPhone, password);
      router.replace("/(auth)/select-elder");
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError("این شماره قبلاً ثبت شده یا مشخصات نامعتبر است. اگر حساب دارید، وارد شوید.");
      } else {
        setError("ایجاد حساب انجام نشد. اتصال اینترنت خود را بررسی کنید.");
      }
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
