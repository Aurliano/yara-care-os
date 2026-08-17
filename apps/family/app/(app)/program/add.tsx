import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { AppText, Button, Card, Screen, TextField, TopAppBar } from "../../../src/components";
import { t } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import { useElderStore } from "../../../src/stores/elderStore";
import { createCareActivity, createPrescription } from "../../../src/api/endpoints/care";
import { queryKeys } from "../../../src/api/queryKeys";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";
import { firstParam } from "../../../src/navigation/params";
import { resolveCareWorkflowDefinitionId } from "../../../src/services/program/workflowDefinition";
import { combineTehranDateTime, onceRecurrence, TEHRAN_TIMEZONE, todayPartsInTehran } from "../../../src/services/program/onceSchedule";

export default function AddCareScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const params = useLocalSearchParams<{ kind?: string }>();
  const kind = firstParam(params.kind) === "appointment" ? "appointment" : "medication";
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();
  const today = todayPartsInTehran();
  const [title, setTitle] = useState("");
  const [dosage, setDosage] = useState("");
  const [description, setDescription] = useState("");
  const [date, setDate] = useState(today.date);
  const [time, setTime] = useState(today.time);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!can(PERMISSIONS.MANAGE_MEDICATION)) {
    return <PermissionDenied />;
  }

  async function onSave() {
    if (!elderId) {
      return;
    }
    const startAt = combineTehranDateTime(date, time);
    if (!startAt) {
      setError(t.invalidDateTime);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const workflowId = await resolveCareWorkflowDefinitionId(elderId);
      if (!workflowId) {
        setError(t.programNotEnabled);
        return;
      }
      if (kind === "appointment") {
        await createCareActivity(elderId, {
          activity_type: "GENERAL",
          workflow_definition_id: workflowId,
          recurrence_definition: onceRecurrence(),
          timezone_name: TEHRAN_TIMEZONE,
          start_at: startAt,
          display_title: title.trim(),
        });
      } else {
        await createPrescription(elderId, {
          workflow_definition_id: workflowId,
          recurrence_definition: onceRecurrence(),
          timezone_name: TEHRAN_TIMEZONE,
          start_at: startAt,
          display_title: title.trim(),
          medication_reference: title.trim(),
          dosage_information: dosage.trim() || t.asDirected,
          elder_friendly_description: description.trim() || title.trim(),
        });
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.careActivities(elderId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.prescriptions(elderId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(elderId) }),
      ]);
      router.back();
    } catch {
      setError(t.errorBody);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <TopAppBar title={kind === "appointment" ? t.addAppointment : t.addMedication} showBack />
      <Card>
        <View style={styles.form}>
          <TextField label={t.title} value={title} onChangeText={setTitle} persianValue={false} />
          {kind === "medication" ? (
            <>
              <TextField label={t.dosage} value={dosage} onChangeText={setDosage} persianValue={false} />
              <TextField
                label={t.description}
                value={description}
                onChangeText={setDescription}
                persianValue={false}
              />
            </>
          ) : null}
          <TextField label={t.occurrenceDate} value={date} onChangeText={setDate} />
          <TextField label={t.occurrenceTime} value={time} onChangeText={setTime} keyboardType="numeric" />
          <AppText variant="caption" color={colors.textMuted}>
            {t.dateHint}
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
