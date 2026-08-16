import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { t } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import { AppText, Button, Card, Screen, TextField, TopAppBar } from "../../src/components";
import { createElder } from "../../src/api/endpoints/identity";
import { queryKeys } from "../../src/api/queryKeys";
import { useElderStore } from "../../src/stores/elderStore";
import { isPermissionDenied } from "../../src/api/errors";

export default function CreateElderScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const selectElder = useElderStore((state) => state.selectElder);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit() {
    setLoading(true);
    setError(null);
    try {
      const elder = await createElder({ full_name: name.trim() });
      await queryClient.invalidateQueries({ queryKey: queryKeys.elders });
      await selectElder(elder.id);
      router.replace("/(app)/(tabs)");
    } catch (err) {
      setError(isPermissionDenied(err) ? t.accessDenied : "ایجاد پرونده انجام نشد.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <TopAppBar title={t.setupElder} showBell={false} showBack />
      <AppText variant="body" color={colors.textSecondary}>
        ایجاد پرونده فقط اگر سرور برای حساب شما مجاز بداند موفق می‌شود. همه کاربران لزوماً این مجوز را ندارند.
      </AppText>
      <Card>
        <View style={styles.form}>
          <TextField label={t.elderName} value={name} onChangeText={setName} persianValue={false} />
          {error ? (
            <AppText variant="caption" color={colors.error}>
              {error}
            </AppText>
          ) : null}
          <Button label={t.createElder} onPress={() => void onSubmit()} loading={loading} disabled={!name.trim()} />
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  form: { gap: spacing.md },
});
