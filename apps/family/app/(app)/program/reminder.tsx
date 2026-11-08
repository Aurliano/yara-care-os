import { useState } from "react";
import {
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AppText, Button, Card, Screen, TopAppBar } from "../../../src/components";
import { Icon } from "../../../src/components/Icon";
import { t } from "../../../src/i18n";
import { toPersianDigits } from "../../../src/i18n/numerals";
import { colors, radius, spacing } from "../../../src/theme/tokens";
import { useElderStore } from "../../../src/stores/elderStore";
import { skipOccurrence } from "../../../src/api/endpoints/scheduling";
import { getElder } from "../../../src/api/endpoints/identity";
import { queryKeys } from "../../../src/api/queryKeys";
import { firstParam } from "../../../src/navigation/params";
import { snoozeMedicationAlarm } from "../../../src/services/medication/alarmScheduler";

export default function ReminderScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const elderId = useElderStore((s) => s.selectedElderId);

  const rawParams = useLocalSearchParams<{
    medicationTitle?: string;
    dosage?: string;
    timeLabel?: string;
    instructions?: string;
    occurrenceId?: string;
    activityId?: string;
  }>();

  const medicationTitle = firstParam(rawParams.medicationTitle) || "داروی تجویزی";
  const dosage = firstParam(rawParams.dosage) || "";
  const timeLabel = firstParam(rawParams.timeLabel) || "هم‌اکنون";
  const instructions = firstParam(rawParams.instructions) || "";
  const occurrenceId = firstParam(rawParams.occurrenceId) || "";

  const elderQuery = useQuery({
    queryKey: elderId ? queryKeys.elder(elderId) : ["elder", "none"],
    queryFn: () => getElder(elderId as string),
    enabled: Boolean(elderId),
  });

  const [statusState, setStatusState] = useState<"IDLE" | "TAKEN" | "SNOOZED" | "SKIPPED">("IDLE");
  const [loading, setLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const targetElderName = elderQuery.data?.full_name || "عزیزتان";

  async function handleTake() {
    setLoading(true);
    try {
      setStatusState("TAKEN");
      setFeedbackMessage(t.takenConfirmationSuccess);
      if (elderId) {
        await queryClient.invalidateQueries({ queryKey: queryKeys.careActivities(elderId) });
      }
      setTimeout(() => {
        router.back();
      }, 1200);
    } catch {
      setStatusState("IDLE");
    } finally {
      setLoading(false);
    }
  }

  function handleSnooze() {
    setLoading(true);
    setStatusState("SNOOZED");
    setFeedbackMessage(t.snoozeSuccess);
    void snoozeMedicationAlarm({
      id: occurrenceId || `reminder-${Date.now()}`,
      title: medicationTitle,
      dosage,
      timeLabel,
    });
    setTimeout(() => {
      router.back();
    }, 1200);
    setLoading(false);
  }

  async function handleSkip() {
    setLoading(true);
    try {
      if (occurrenceId) {
        await skipOccurrence(occurrenceId);
      }
      setStatusState("SKIPPED");
      setFeedbackMessage(t.skipDoseSuccess);
      if (elderId) {
        await queryClient.invalidateQueries({ queryKey: queryKeys.careActivities(elderId) });
      }
      setTimeout(() => {
        router.back();
      }, 1200);
    } catch {
      setStatusState("SKIPPED");
      setFeedbackMessage(t.skipDoseSuccess);
      setTimeout(() => {
        router.back();
      }, 1200);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen style={styles.screenBg}>
      <TopAppBar
        title={t.reminderScreenTitle}
        showBack
        showBell={false}
      />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Soft pulse header container */}
        <View style={styles.headerHero}>
          <View style={styles.iconCircle}>
            <Icon name="medication" color={colors.primary} width={36} height={36} />
          </View>
          <AppText variant="headline" align="center" style={styles.heroTitle}>
            {t.timeToTakeMedication}
          </AppText>
          <View style={styles.elderBadge}>
            <AppText variant="caption" color={colors.textSecondary} align="center">
              {`${t.elderNamePrefix}: ${targetElderName}`}
            </AppText>
          </View>
        </View>

        {/* Feedback message banner if user just clicked an action */}
        {feedbackMessage ? (
          <View
            style={[
              styles.feedbackBanner,
              statusState === "TAKEN"
                ? styles.feedbackSuccess
                : statusState === "SNOOZED"
                ? styles.feedbackSnoozed
                : styles.feedbackSkipped,
            ]}
          >
            <Icon
              name={statusState === "TAKEN" ? "check" : "info"}
              color={statusState === "TAKEN" ? colors.success : colors.warningBrown}
              width={20}
              height={20}
            />
            <AppText
              variant="label"
              color={statusState === "TAKEN" ? colors.successOn : colors.warningBrown}
              style={{ flex: 1 }}
            >
              {feedbackMessage}
            </AppText>
          </View>
        ) : null}

        {/* Medication Details Card */}
        <Card accent="medication" style={styles.medCard}>
          <View style={styles.medTitleRow}>
            <View style={{ flex: 1 }}>
              <AppText variant="title" color={colors.primary}>
                {medicationTitle}
              </AppText>
              {dosage ? (
                <View style={styles.dosageRow}>
                  <AppText variant="caption" color={colors.textMuted}>
                    {t.dosageTitle}:
                  </AppText>
                  <AppText variant="body" color={colors.textSecondary} style={{ fontWeight: "700" }}>
                    {dosage}
                  </AppText>
                </View>
              ) : null}
            </View>

            <View style={styles.timeBadge}>
              <Icon name="info" color={colors.primary} width={16} height={16} />
              <AppText variant="time" color={colors.primary}>
                {toPersianDigits(timeLabel)}
              </AppText>
            </View>
          </View>

          {instructions ? (
            <View style={styles.instructionsContainer}>
              <View style={styles.instructionsHeader}>
                <Icon name="attention" color={colors.textMuted} width={14} height={14} />
                <AppText variant="caption" color={colors.textMuted}>
                  {t.instructionsTitle}
                </AppText>
              </View>
              <AppText variant="body" color={colors.textSecondary} style={styles.instructionsText}>
                {instructions}
              </AppText>
            </View>
          ) : null}
        </Card>

        {/* Big accessible action buttons */}
        <View style={styles.actionsContainer}>
          {/* 1. Primary Action: Taken */}
          <Button
            label={t.takenAction}
            variant="primary"
            icon="check"
            onPress={handleTake}
            loading={loading && statusState === "TAKEN"}
            disabled={loading}
            style={styles.mainActionButton}
          />

          {/* 2. Secondary Action: Snooze 10 minutes */}
          <Button
            label={t.snoozeAction}
            variant="secondary"
            icon="info"
            onPress={handleSnooze}
            loading={loading && statusState === "SNOOZED"}
            disabled={loading}
            style={styles.secondaryActionButton}
          />

          {/* 3. Ghost / Skip Action: Skip dose */}
          <Button
            label={t.skipDoseAction}
            variant="ghost"
            onPress={handleSkip}
            loading={loading && statusState === "SKIPPED"}
            disabled={loading}
            style={styles.skipActionButton}
          />
        </View>
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screenBg: {
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.screen,
    paddingBottom: 40,
    gap: spacing.lg,
  },
  headerHero: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.md,
    gap: spacing.sm,
  },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.surfaceSoft,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.xs,
    borderWidth: 2,
    borderColor: colors.medicationAccent,
  },
  heroTitle: {
    fontSize: 22,
    lineHeight: 32,
    color: colors.text,
  },
  elderBadge: {
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  medCard: {
    padding: spacing.md,
    gap: spacing.md,
    backgroundColor: colors.surface,
  },
  medTitleRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: spacing.sm,
  },
  dosageRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  timeBadge: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  instructionsContainer: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.sm,
    padding: spacing.sm,
    gap: 4,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  instructionsHeader: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
  },
  instructionsText: {
    lineHeight: 24,
    paddingHorizontal: 4,
  },
  actionsContainer: {
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  mainActionButton: {
    minHeight: 64, // Large accessible touch target per UI guidelines
    backgroundColor: colors.primary,
  },
  secondaryActionButton: {
    minHeight: 56,
    borderColor: colors.primary,
  },
  skipActionButton: {
    minHeight: 48,
  },
  feedbackBanner: {
    flexDirection: "row-reverse",
    alignItems: "center",
    padding: spacing.md,
    borderRadius: radius.md,
    gap: spacing.sm,
    borderWidth: 1,
  },
  feedbackSuccess: {
    backgroundColor: colors.successSoft,
    borderColor: colors.success,
  },
  feedbackSnoozed: {
    backgroundColor: colors.warningSoft,
    borderColor: colors.warningBorder,
  },
  feedbackSkipped: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.borderStrong,
  },
});
