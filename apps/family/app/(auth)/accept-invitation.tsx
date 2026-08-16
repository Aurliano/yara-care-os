import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { acceptInvitation, listElders } from "../../src/api/endpoints/identity";
import { mapInvitationError } from "../../src/api/errors";
import { queryKeys } from "../../src/api/queryKeys";
import { AppText, Button, Card, Screen, TextField } from "../../src/components";
import { Icon } from "../../src/components/Icon";
import { t } from "../../src/i18n";
import { toLatinDigits } from "../../src/i18n/numerals";
import { colors, spacing } from "../../src/theme/tokens";
import { useElderStore } from "../../src/stores/elderStore";
import { useState } from "react";
import { StyleSheet, View } from "react-native";

export default function AcceptInvitationScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const selectElder = useElderStore((state) => state.selectElder);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onAccept() {
    setLoading(true);
    setError(null);
    try {
      await acceptInvitation(toLatinDigits(code).trim());
      const elders = await listElders();
      await queryClient.setQueryData(queryKeys.elders, elders);
      if (elders.length === 1) {
        await selectElder(elders[0].id);
        await queryClient.invalidateQueries({ queryKey: ["elder"] });
        router.replace("/(app)/(tabs)");
        return;
      }
      router.replace("/(auth)/select-elder");
    } catch (err) {
      setError(mapInvitationError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <View style={styles.iconWrap}>
        <Icon name="envelope" width={36} height={24} color={colors.primary} />
      </View>
      <AppText variant="headline" color={colors.primary} align="center">
        {t.inviteHeadline}
      </AppText>
      <AppText variant="body" color={colors.textSecondary} align="center">
        کد دعوتی که برای شما ارسال شده را وارد کنید. پیش‌نمایش نام سالمند تا پیش از پذیرش در سرور موجود نیست.
      </AppText>
      <Card>
        <View style={styles.form}>
          <TextField label={t.inviteCode} value={code} onChangeText={setCode} icon="envelope" />
          {error ? (
            <AppText variant="caption" color={colors.error} align="center">
              {error}
            </AppText>
          ) : null}
          <Button label={t.acceptInviteCta} onPress={() => void onAccept()} loading={loading} />
          <Button label={t.notNow} variant="secondary" onPress={() => router.back()} />
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  iconWrap: {
    alignSelf: "center",
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#89F5E7",
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.xl,
    marginBottom: spacing.lg,
  },
  form: { gap: spacing.md },
});
