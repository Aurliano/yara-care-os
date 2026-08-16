import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { AppText, Button, Card, Screen, TextField, TopAppBar } from "../../../src/components";
import { t } from "../../../src/i18n";
import { toLatinDigits } from "../../../src/i18n/numerals";
import { colors, spacing } from "../../../src/theme/tokens";
import { useElderStore } from "../../../src/stores/elderStore";
import { listCareActivities, createPrescription } from "../../../src/api/endpoints/care";
import { queryKeys } from "../../../src/api/queryKeys";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";

export default function AddMedicationScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();
  const activities = useQuery({
    queryKey: elderId ? queryKeys.careActivities(elderId) : ["care-activities"],
    enabled: Boolean(elderId),
    queryFn: () => listCareActivities(elderId as string),
  });
  const [title, setTitle] = useState("");
  const [dosage, setDosage] = useState("");
  const [description, setDescription] = useState("");
  const [time, setTime] = useState("08:00");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!can(PERMISSIONS.MANAGE_MEDICATION)) {
    return <PermissionDenied />;
  }

  const workflowId = activities.data?.find((item) => item.activity_type === "MEDICATION")?.workflow_definition_id;

  async function onSave() {
    if (!elderId) {
      return;
    }
    if (!workflowId) {
      setError(t.workflowCatalogMissing);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await createPrescription(elderId, {
        workflow_definition_id: workflowId,
        recurrence_definition: { type: "daily", time: toLatinDigits(time) },
        timezone_name: "Asia/Tehran",
        start_at: new Date().toISOString(),
        display_title: title,
        medication_reference: title,
        dosage_information: dosage,
        elder_friendly_description: description,
      });
      router.back();
    } catch {
      setError(t.errorBody);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <TopAppBar title={t.addMedication} showBack showBell={false} />
      <Card>
        <View style={styles.form}>
          <TextField label={t.title} value={title} onChangeText={setTitle} persianValue={false} />
          <TextField label={t.dosage} value={dosage} onChangeText={setDosage} persianValue={false} />
          <TextField label={t.description} value={description} onChangeText={setDescription} persianValue={false} />
          <TextField label={t.dailyTime} value={time} onChangeText={setTime} keyboardType="numeric" />
          <AppText variant="caption" color={colors.textMuted}>
            {t.regimenGap}
          </AppText>
          {error ? (
            <AppText variant="caption" color={colors.error}>
              {error}
            </AppText>
          ) : null}
          <Button label={t.save} onPress={() => void onSave()} loading={loading} disabled={!title.trim()} />
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  form: { gap: spacing.md },
});
