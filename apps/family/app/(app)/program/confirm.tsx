import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { endCareActivity } from "../../../src/api/endpoints/care";
import { createScheduleException } from "../../../src/api/endpoints/scheduling";
import { AppText, Button, Card, Screen, TextField, TopAppBar } from "../../../src/components";
import { t } from "../../../src/i18n";
import { toLatinDigits } from "../../../src/i18n/numerals";
import { firstParam } from "../../../src/navigation/params";
import { colors, spacing } from "../../../src/theme/tokens";

export default function ConfirmScreen() {
  const router = useRouter();
  const raw = useLocalSearchParams<{
    activityId: string;
    scheduleId?: string;
    originalTime?: string;
    kind: "end" | "reschedule" | "skip";
  }>();
  const params = {
    activityId: firstParam(raw.activityId) ?? "",
    scheduleId: firstParam(raw.scheduleId),
    originalTime: firstParam(raw.originalTime),
    kind: firstParam(raw.kind),
  };
  const [time, setTime] = useState("20:00");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onConfirm() {
    setLoading(true);
    setError(null);
    try {
      if (params.kind === "end") {
        await endCareActivity(params.activityId);
      } else if (params.kind === "reschedule" && params.scheduleId && params.originalTime) {
        const [h, m] = toLatinDigits(time).split(":");
        const original = new Date(params.originalTime);
        original.setHours(Number(h), Number(m), 0, 0);
        await createScheduleException(params.scheduleId, {
          original_time: params.originalTime,
          exception_type: "RESCHEDULE",
          replacement_time: original.toISOString(),
        });
      }
      router.back();
    } catch {
      setError(t.errorBody);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <TopAppBar title={t.confirm} showBack showBell={false} />
      <Card>
        <AppText variant="title">
          {params.kind === "end" ? t.endActivity : t.rescheduleOnce}
        </AppText>
        {params.kind === "reschedule" ? (
          <TextField label={t.replacementTime} value={time} onChangeText={setTime} keyboardType="numeric" />
        ) : (
          <AppText variant="body" color={colors.textSecondary}>
            این برنامه برای سالمند پایان می‌یابد.
          </AppText>
        )}
        {error ? (
          <AppText variant="caption" color={colors.error}>
            {error}
          </AppText>
        ) : null}
        <View style={styles.row}>
          <Button label={t.confirm} onPress={() => void onConfirm()} loading={loading} />
          <Button label={t.cancel} variant="secondary" onPress={() => router.back()} />
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.sm, marginTop: spacing.md },
});
