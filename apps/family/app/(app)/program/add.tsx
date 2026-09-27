import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { AppText, Button, Card, Icon, Screen, TextField, TopAppBar } from "../../../src/components";
import { t } from "../../../src/i18n";
import { toLatinDigits, toPersianDigits } from "../../../src/i18n/numerals";
import { colors, radius, spacing } from "../../../src/theme/tokens";
import { useElderStore } from "../../../src/stores/elderStore";
import { createCareActivity, createPrescription } from "../../../src/api/endpoints/care";
import { queryKeys } from "../../../src/api/queryKeys";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";
import { firstParam } from "../../../src/navigation/params";
import { resolveCareWorkflowDefinitionId } from "../../../src/services/program/workflowDefinition";
import {
  generateIdempotencyKey,
  getTodayJalali,
  JALALI_WEEKDAYS,
  jalaliToTehranIso,
  parseJalaliDateString,
  TEHRAN_TIMEZONE,
} from "../../../src/services/program/jalali";

type FrequencyType = "daily" | "specific_days" | "every_n_days" | "once";

const TIME_PRESETS = ["08:00", "12:00", "18:00", "22:00"];

export default function AddCareScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const params = useLocalSearchParams<{ kind?: string }>();
  const kind = firstParam(params.kind) === "appointment" ? "appointment" : "medication";
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();

  const todayJalali = getTodayJalali();
  const [idempotencyKey] = useState(() => generateIdempotencyKey());

  const [title, setTitle] = useState("");
  const [dosage, setDosage] = useState("");
  const [description, setDescription] = useState("");
  const [frequency, setFrequency] = useState<FrequencyType>("daily");

  const [startDate, setStartDate] = useState(todayJalali.formatted);
  const [hasEndDate, setHasEndDate] = useState(false);
  const [endDate, setEndDate] = useState("");

  const [times, setTimes] = useState<string[]>(["08:00"]);
  const [newTimeInput, setNewTimeInput] = useState("14:00");
  const [singleTime, setSingleTime] = useState("08:00");

  const [selectedWeekdays, setSelectedWeekdays] = useState<string[]>(["SAT", "MON", "WED"]);
  const [everyNDays, setEveryNDays] = useState("2");

  const [error, setError] = useState<string | null>(null);
  const [timeError, setTimeError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!can(PERMISSIONS.MANAGE_MEDICATION)) {
    return <PermissionDenied />;
  }

  function handleAddTimeSlot(timeCandidate?: string) {
    const raw = timeCandidate ?? newTimeInput;
    const clean = toLatinDigits(raw).trim();
    setTimeError(null);

    const match = /^(\d{1,2}):(\d{2})$/.exec(clean);
    if (!match) {
      setTimeError(t.timeSlotInvalid);
      return;
    }
    const h = Number(match[1]);
    const m = Number(match[2]);
    if (h < 0 || h > 23 || m < 0 || m > 59) {
      setTimeError(t.timeSlotInvalid);
      return;
    }
    const formatted = `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;

    if (times.includes(formatted)) {
      setTimeError(t.timeSlotDuplicate);
      return;
    }

    setTimes((prev) => [...prev, formatted].sort());
  }

  function handleRemoveTimeSlot(target: string) {
    setTimeError(null);
    setTimes((prev) => prev.filter((tStr) => tStr !== target));
  }

  function toggleWeekday(code: string) {
    setSelectedWeekdays((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  async function onSave() {
    if (!elderId) {
      return;
    }
    setError(null);

    if (!title.trim()) {
      setError("لطفاً عنوان دارو یا برنامه را وارد کنید.");
      return;
    }

    const firstSlot = frequency === "once" ? singleTime : times[0] ?? "08:00";
    const startIso = jalaliToTehranIso(startDate, firstSlot);
    if (!startIso) {
      setError(t.invalidDateTime);
      return;
    }

    let endIso: string | null = null;
    if (hasEndDate) {
      if (!endDate.trim()) {
        setError("لطفاً تاریخ پایان را وارد کنید.");
        return;
      }
      endIso = jalaliToTehranIso(endDate, "23:59");
      if (!endIso) {
        setError(t.invalidDateTime);
        return;
      }
      const sParsed = parseJalaliDateString(startDate);
      const eParsed = parseJalaliDateString(endDate);
      if (sParsed && eParsed) {
        const sVal = sParsed.year * 10000 + sParsed.month * 100 + sParsed.day;
        const eVal = eParsed.year * 10000 + eParsed.month * 100 + eParsed.day;
        if (eVal < sVal) {
          setError(t.endDateBeforeStart);
          return;
        }
      }
    }

    if (frequency !== "once" && times.length === 0) {
      setError(t.timeSlotsEmpty);
      return;
    }

    let recurrenceDef: Record<string, unknown>;
    if (frequency === "once") {
      recurrenceDef = { type: "once" };
    } else if (frequency === "daily") {
      recurrenceDef = { type: "daily", times };
    } else if (frequency === "specific_days") {
      if (selectedWeekdays.length === 0) {
        setError(t.weekdaysEmpty);
        return;
      }
      recurrenceDef = { type: "specific_days", days: selectedWeekdays, times };
    } else {
      const everyNum = Number(toLatinDigits(everyNDays).trim());
      if (!everyNum || everyNum <= 0) {
        setError(t.intervalInvalid);
        return;
      }
      recurrenceDef = { type: "every_n_days", every: everyNum, times };
    }

    setLoading(true);
    try {
      const workflowId = await resolveCareWorkflowDefinitionId(elderId);
      if (!workflowId) {
        setError(t.programNotEnabled);
        return;
      }

      if (kind === "appointment") {
        await createCareActivity(
          elderId,
          {
            activity_type: "GENERAL",
            workflow_definition_id: workflowId,
            recurrence_definition: recurrenceDef,
            timezone_name: TEHRAN_TIMEZONE,
            start_at: startIso,
            end_at: endIso,
            display_title: title.trim(),
            display_subtitle: dosage.trim() || undefined,
          },
          { idempotencyKey },
        );
      } else {
        await createPrescription(
          elderId,
          {
            workflow_definition_id: workflowId,
            recurrence_definition: recurrenceDef,
            timezone_name: TEHRAN_TIMEZONE,
            start_at: startIso,
            end_at: endIso,
            display_title: title.trim(),
            medication_reference: title.trim(),
            dosage_information: dosage.trim() || t.asDirected,
            elder_friendly_description: description.trim() || title.trim(),
          },
          { idempotencyKey },
        );
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
      <ScrollView contentContainerStyle={styles.scroll}>
        <Card>
          <View style={styles.form}>
            {/* Title & Medication Info */}
            <TextField
              label={kind === "appointment" ? "عنوان قرار یا یادآوری" : "نام دارو"}
              value={title}
              onChangeText={setTitle}
              persianValue={false}
              placeholder={kind === "appointment" ? "مثلاً معاینه پزشک" : "مثلاً آسپرین ۸۱"}
            />

            {kind === "medication" ? (
              <>
                <TextField
                  label={t.dosage}
                  value={dosage}
                  onChangeText={setDosage}
                  persianValue={false}
                  placeholder="مثلاً ۱ عدد بعد از صبحانه"
                />
                <TextField
                  label={t.description}
                  value={description}
                  onChangeText={setDescription}
                  persianValue={false}
                  placeholder="توضیح کوتاه و خوانا برای سالمند"
                />
              </>
            ) : null}

            {/* Frequency Selection */}
            <View style={styles.sectionWrap}>
              <AppText variant="caption" color={colors.text}>
                {t.frequency}
              </AppText>
              <View style={styles.chipRow}>
                {(
                  [
                    { key: "daily", label: t.freqDaily },
                    { key: "specific_days", label: t.freqSpecificDays },
                    { key: "every_n_days", label: t.freqEveryNDays },
                    { key: "once", label: t.freqOnce },
                  ] as const
                ).map((item) => {
                  const active = frequency === item.key;
                  return (
                    <Pressable
                      key={item.key}
                      style={[styles.chip, active && styles.chipActive]}
                      onPress={() => setFrequency(item.key)}
                      accessibilityRole="button"
                    >
                      <AppText
                        variant="caption"
                        color={active ? colors.primaryOn : colors.textSecondary}
                      >
                        {item.label}
                      </AppText>
                    </Pressable>
                  );
                })}
              </View>
            </View>

            {/* Weekdays Selector */}
            {frequency === "specific_days" ? (
              <View style={styles.sectionWrap}>
                <AppText variant="caption" color={colors.text}>
                  {t.selectWeekdays}
                </AppText>
                <View style={styles.weekdayRow}>
                  {JALALI_WEEKDAYS.map((w) => {
                    const selected = selectedWeekdays.includes(w.code);
                    return (
                      <Pressable
                        key={w.code}
                        style={[styles.weekdayChip, selected && styles.weekdayChipActive]}
                        onPress={() => toggleWeekday(w.code)}
                        accessibilityRole="button"
                      >
                        <AppText
                          variant="caption"
                          color={selected ? colors.primaryOn : colors.textSecondary}
                        >
                          {w.label}
                        </AppText>
                      </Pressable>
                    );
                  })}
                </View>
              </View>
            ) : null}

            {/* Interval in Days */}
            {frequency === "every_n_days" ? (
              <View style={styles.sectionWrap}>
                <TextField
                  label={t.intervalDays}
                  value={everyNDays}
                  onChangeText={setEveryNDays}
                  keyboardType="numeric"
                  placeholder="۲"
                />
                <AppText variant="caption" color={colors.textMuted}>
                  {t.intervalHint}
                </AppText>
              </View>
            ) : null}

            {/* Multi-Time Slots Section */}
            {frequency !== "once" ? (
              <View style={styles.sectionWrap}>
                <AppText variant="caption" color={colors.text}>
                  {t.timeSlots}
                </AppText>

                {/* Existing time slot chips */}
                <View style={styles.slotBadgeRow}>
                  {times.map((slot) => (
                    <View key={slot} style={styles.slotBadge}>
                      <AppText variant="body" color={colors.primary}>
                        {toPersianDigits(slot)}
                      </AppText>
                      <Pressable
                        onPress={() => handleRemoveTimeSlot(slot)}
                        hitSlop={8}
                        accessibilityLabel={`حذف ${slot}`}
                        accessibilityRole="button"
                      >
                        <AppText variant="body" color={colors.error} style={{ fontWeight: "700", marginHorizontal: 4 }}>
                          ✕
                        </AppText>
                      </Pressable>
                    </View>
                  ))}
                </View>

                {/* Add new time slot */}
                <View style={styles.addSlotBox}>
                  <View style={styles.addSlotInputRow}>
                    <View style={{ flex: 1 }}>
                      <TextField
                        label="ساعت نوبت جدید (۲۴ ساعته)"
                        value={newTimeInput}
                        onChangeText={setNewTimeInput}
                        keyboardType="numeric"
                        placeholder="۰۸:۰۰"
                      />
                    </View>
                    <Pressable
                      style={styles.addSlotBtn}
                      onPress={() => handleAddTimeSlot()}
                      accessibilityRole="button"
                    >
                      <AppText variant="caption" color={colors.primaryOn}>
                        {t.addTimeSlot}
                      </AppText>
                    </Pressable>
                  </View>

                  {/* Preset quick buttons */}
                  <View style={styles.presetRow}>
                    <AppText variant="caption" color={colors.textMuted}>
                      ساعت‌های متداول:
                    </AppText>
                    {TIME_PRESETS.map((preset) => (
                      <Pressable
                        key={preset}
                        style={styles.presetChip}
                        onPress={() => handleAddTimeSlot(preset)}
                      >
                        <AppText variant="caption" color={colors.secondary}>
                          {toPersianDigits(preset)}
                        </AppText>
                      </Pressable>
                    ))}
                  </View>

                  {timeError ? (
                    <AppText variant="caption" color={colors.error}>
                      {timeError}
                    </AppText>
                  ) : null}
                </View>
              </View>
            ) : (
              <TextField
                label={t.occurrenceTime}
                value={singleTime}
                onChangeText={setSingleTime}
                keyboardType="numeric"
                placeholder="۰۸:۰۰"
              />
            )}

            {/* Dates in Jalali */}
            <View style={styles.sectionWrap}>
              <TextField
                label={t.startDate}
                value={startDate}
                onChangeText={setStartDate}
                placeholder="۱۴۰۵/۰۷/۰۲"
              />
              <AppText variant="caption" color={colors.textMuted}>
                {t.jalaliDateHint}
              </AppText>
            </View>

            {/* End Date Toggle */}
            <Pressable
              style={styles.toggleRow}
              onPress={() => setHasEndDate((val) => !val)}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: hasEndDate }}
            >
              <View style={[styles.checkbox, hasEndDate && styles.checkboxActive]}>
                {hasEndDate ? (
                  <Icon name="check" color={colors.primaryOn} width={14} height={14} />
                ) : null}
              </View>
              <AppText variant="body" color={colors.text}>
                {t.hasEndDate}
              </AppText>
            </Pressable>

            {hasEndDate ? (
              <TextField
                label={t.endDate}
                value={endDate}
                onChangeText={setEndDate}
                placeholder="۱۴۰۵/۰۸/۰۲"
              />
            ) : null}

            {/* Global Error Banner */}
            {error ? (
              <AppText variant="caption" color={colors.error}>
                {error}
              </AppText>
            ) : null}

            {/* Save Button */}
            <Button
              label={t.save}
              onPress={() => void onSave()}
              loading={loading}
              disabled={!title.trim()}
            />
          </View>
        </Card>
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  scroll: {
    paddingBottom: spacing.xl,
  },
  form: {
    gap: spacing.md,
  },
  sectionWrap: {
    gap: spacing.xs,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
  },
  chip: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm + 4,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceSoft,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  chipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  weekdayRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
  },
  weekdayChip: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.sm,
    backgroundColor: colors.surfaceSoft,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  weekdayChipActive: {
    backgroundColor: colors.secondary,
    borderColor: colors.secondary,
  },
  slotBadgeRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
    marginVertical: spacing.xs,
  },
  slotBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs + 2,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm + 2,
    backgroundColor: colors.successSoft,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.medicationAccent,
  },
  addSlotBox: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: radius.sm,
    padding: spacing.sm,
    gap: spacing.xs,
  },
  addSlotInputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: spacing.sm,
  },
  addSlotBtn: {
    height: 44,
    backgroundColor: colors.primary,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    justifyContent: "center",
    alignItems: "center",
  },
  presetRow: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  presetChip: {
    paddingVertical: 2,
    paddingHorizontal: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.borderMuted,
  },
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.xs,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: radius.sm - 4,
    borderWidth: 2,
    borderColor: colors.borderStrong,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: colors.surface,
  },
  checkboxActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
});
