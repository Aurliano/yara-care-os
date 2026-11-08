import { useState, useMemo } from "react";
import {
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import {
  AppText,
  Button,
  Card,
  Screen,
  TextField,
  TopAppBar,
  WheelPicker,
} from "../../../src/components";
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
  addDaysToJalali,
  generateIdempotencyKey,
  getTodayJalali,
  JALALI_MONTH_NAMES,
  JALALI_WEEKDAYS,
  jalaliToTehranIso,
  parseJalaliDateString,
  TEHRAN_TIMEZONE,
} from "../../../src/services/program/jalali";
import {
  DRUG_FORMS,
  DrugForm,
  DrugItem,
  searchDrugs,
} from "../../../src/services/medication/drugDatabase";
import { scheduleMedicationAlarm } from "../../../src/services/medication/alarmScheduler";

type FrequencyType = "daily" | "specific_days" | "every_n_days" | "once";
type DurationOption = "ongoing" | "7_days" | "14_days" | "30_days";

const MEDICATION_ICONS: Record<DrugForm, any> = {
  tablet: require("../../../assets/medications/tablet.png"),
  capsule: require("../../../assets/medications/capsule.png"),
  syrup: require("../../../assets/medications/syrup.png"),
  drops: require("../../../assets/medications/drops.png"),
  injection: require("../../../assets/medications/injection.png"),
  ointment: require("../../../assets/medications/ointment.png"),
  inhaler: require("../../../assets/medications/inhaler.png"),
  other: require("../../../assets/medications/other.png"),
};

const TIME_PRESETS = [
  { label: "صبح (۰۸:۰۰)", value: "08:00" },
  { label: "ظهر (۱۲:۰۰)", value: "12:00" },
  { label: "عصر (۱۸:۰۰)", value: "18:00" },
  { label: "شب (۲۲:۰۰)", value: "22:00" },
];

const MEAL_INSTRUCTIONS = [
  "بعد از غذا",
  "همراه با غذا",
  "قبل از غذا (ناشتا)",
  "قبل از خواب",
  "ساعت معین و منظم",
];

const HOURS = Array.from({ length: 24 }, (_, i) => ({
  label: toPersianDigits(String(i).padStart(2, "0")),
  value: i,
}));

const MINUTES = Array.from({ length: 12 }, (_, i) => {
  const m = i * 5;
  return {
    label: toPersianDigits(String(m).padStart(2, "0")),
    value: m,
  };
});

export default function AddCareScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const params = useLocalSearchParams<{ kind?: string }>();
  const kind = firstParam(params.kind) === "appointment" ? "appointment" : "medication";
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();

  const todayJalali = useMemo(() => getTodayJalali(), []);
  const [idempotencyKey] = useState(() => generateIdempotencyKey());

  // Wizard state: Step 1 to 5
  const [step, setStep] = useState<number>(1);

  // Step 1: Medication Info
  const [title, setTitle] = useState("");
  const [formFactor, setFormFactor] = useState<DrugForm>("tablet");
  const [dosage, setDosage] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showDrugSuggestions, setShowDrugSuggestions] = useState(false);

  // Step 2: Reminder Times
  const [times, setTimes] = useState<string[]>(["08:00"]);
  const [isTimeModalVisible, setIsTimeModalVisible] = useState(false);
  const [pickerHour, setPickerHour] = useState(8);
  const [pickerMinute, setPickerMinute] = useState(0);

  // Step 3: Recurrence
  const [frequency, setFrequency] = useState<FrequencyType>("daily");
  const [selectedWeekdays, setSelectedWeekdays] = useState<string[]>(["SAT", "MON", "WED"]);
  const [everyNDays, setEveryNDays] = useState("2");
  const singleTime = "08:00";

  // Step 4: Dates & Duration
  const [startYear, setStartYear] = useState(todayJalali.year);
  const [startMonth, setStartMonth] = useState(todayJalali.month);
  const [startDay, setStartDay] = useState(todayJalali.day);
  const [durationOption, setDurationOption] = useState<DurationOption>("ongoing");

  // Step 5: Meal Timing & Description
  const [selectedMealInstruction, setSelectedMealInstruction] = useState("بعد از غذا");
  const [additionalNote, setAdditionalNote] = useState("");

  // General Status
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!can(PERMISSIONS.MANAGE_MEDICATION)) {
    return <PermissionDenied />;
  }

  // Filtered drug suggestions
  const drugSuggestions = useMemo(() => {
    if (!searchQuery.trim()) return [];
    return searchDrugs(searchQuery);
  }, [searchQuery]);

  const startDateFormatted = `${startYear}/${String(startMonth).padStart(2, "0")}/${String(startDay).padStart(2, "0")}`;

  function selectDrugItem(item: DrugItem) {
    setTitle(item.nameFa);
    setSearchQuery(item.nameFa);
    setFormFactor(item.defaultForm);
    if (item.commonDosages.length > 0 && !dosage) {
      setDosage(item.commonDosages[0] ?? "");
    }
    if (item.defaultInstructionFa) {
      setSelectedMealInstruction(item.defaultInstructionFa);
    }
    setShowDrugSuggestions(false);
  }

  function handleAddTimeSlot(formatted: string) {
    if (!times.includes(formatted)) {
      setTimes((prev) => [...prev, formatted].sort());
    }
  }

  function handleRemoveTimeSlot(target: string) {
    setTimes((prev) => prev.filter((tStr) => tStr !== target));
  }

  function handleConfirmTimeModal() {
    const formatted = `${String(pickerHour).padStart(2, "0")}:${String(pickerMinute).padStart(2, "0")}`;
    handleAddTimeSlot(formatted);
    setIsTimeModalVisible(false);
  }

  function toggleWeekday(code: string) {
    setSelectedWeekdays((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  function handleSetToday() {
    setStartYear(todayJalali.year);
    setStartMonth(todayJalali.month);
    setStartDay(todayJalali.day);
  }

  function validateCurrentStep(): boolean {
    setError(null);
    if (step === 1) {
      if (!title.trim()) {
        setError(kind === "appointment" ? "لطفاً عنوان نوبت یا ویزیت را وارد کنید." : "لطفاً نام دارو را وارد کنید.");
        return false;
      }
    } else if (step === 2) {
      if (frequency !== "once" && times.length === 0) {
        setError("لطفاً حداقل یک ساعت برای یادآوری دارو انتخاب یا اضافه کنید.");
        return false;
      }
    } else if (step === 3) {
      if (frequency === "specific_days" && selectedWeekdays.length === 0) {
        setError("لطفاً حداقل یک روز از روزهای هفته را انتخاب کنید.");
        return false;
      }
      if (frequency === "every_n_days") {
        const n = Number(toLatinDigits(everyNDays).trim());
        if (!n || n <= 0) {
          setError("لطفاً فاصله زمانی را به درستی مشخص کنید (مثلاً هر ۲ روز).");
          return false;
        }
      }
    } else if (step === 4) {
      const parsed = parseJalaliDateString(startDateFormatted);
      if (!parsed) {
        setError("تاریخ شروع انتخاب شده معتبر نیست.");
        return false;
      }
    }
    return true;
  }

  function handleNext() {
    if (!validateCurrentStep()) return;
    if (step < 5) {
      setStep((prev) => prev + 1);
    } else {
      onFinalSave();
    }
  }

  function handlePrev() {
    setError(null);
    if (step > 1) {
      setStep((prev) => prev - 1);
    } else {
      router.back();
    }
  }

  async function onFinalSave() {
    if (!elderId) return;
    setError(null);

    const firstSlot = frequency === "once" ? singleTime : times[0] ?? "08:00";
    const startIso = jalaliToTehranIso(startDateFormatted, firstSlot);
    if (!startIso) {
      setError(t.invalidDateTime);
      return;
    }

    let calculatedEndDate: string | null = null;
    if (durationOption === "7_days") {
      calculatedEndDate = addDaysToJalali(startDateFormatted, 7);
    } else if (durationOption === "14_days") {
      calculatedEndDate = addDaysToJalali(startDateFormatted, 14);
    } else if (durationOption === "30_days") {
      calculatedEndDate = addDaysToJalali(startDateFormatted, 30);
    }

    let endIso: string | null = null;
    if (calculatedEndDate) {
      endIso = jalaliToTehranIso(calculatedEndDate, "23:59");
    }

    let recurrenceDef: Record<string, unknown>;
    if (frequency === "once") {
      recurrenceDef = { type: "once" };
    } else if (frequency === "daily") {
      recurrenceDef = { type: "daily", times };
    } else if (frequency === "specific_days") {
      recurrenceDef = { type: "specific_days", days: selectedWeekdays, times };
    } else {
      const everyNum = Number(toLatinDigits(everyNDays).trim()) || 2;
      recurrenceDef = { type: "every_n_days", every: everyNum, times };
    }

    const fullDescription = [
      selectedMealInstruction,
      additionalNote.trim(),
    ].filter(Boolean).join(" - ");

    setLoading(true);
    try {
      const workflowId = await resolveCareWorkflowDefinitionId(elderId);

      if (kind === "appointment") {
        await createCareActivity(
          elderId,
          {
            activity_type: "GENERAL",
            workflow_definition_id: workflowId ?? undefined,
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
            workflow_definition_id: workflowId ?? undefined,
            recurrence_definition: recurrenceDef,
            timezone_name: TEHRAN_TIMEZONE,
            start_at: startIso,
            end_at: endIso,
            display_title: title.trim(),
            medication_reference: title.trim(),
            dosage_information: dosage.trim() || t.asDirected,
            elder_friendly_description: fullDescription || title.trim(),
          },
          { idempotencyKey },
        );
      }

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.careActivities(elderId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.prescriptions(elderId) }),
      ]);

      // Schedule local alarms for immediate alert coverage
      try {
        const now = new Date();
        for (const timeStr of times) {
          const [hStr, mStr] = timeStr.split(":");
          const h = parseInt(hStr, 10);
          const m = parseInt(mStr, 10);
          if (isNaN(h) || isNaN(m)) continue;
          const alarmDate = new Date();
          alarmDate.setHours(h, m, 0, 0);
          let targetMs = alarmDate.getTime();
          if (targetMs <= now.getTime()) {
            targetMs += 24 * 60 * 60 * 1000;
          }
          await scheduleMedicationAlarm({
            id: `local-${elderId}-${Date.now()}-${h}-${m}`,
            title: title.trim(),
            dosage: dosage.trim() || "",
            timeLabel: timeStr,
            timestampMs: targetMs,
          });
        }
      } catch (_e) {
        // Alarm registration fallback
      }

      router.back();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "ثبت دارو یا برنامه با خطا مواجه شد. لطفاً دوباره تلاش کنید.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  // Day items for Jalali day picker (1 to 31)
  const daysItems = useMemo(() => {
    const maxDays = startMonth <= 6 ? 31 : startMonth <= 11 ? 30 : 29;
    return Array.from({ length: maxDays }, (_, i) => ({
      label: toPersianDigits(String(i + 1)),
      value: i + 1,
    }));
  }, [startMonth]);

  const monthItems = useMemo(() => {
    return JALALI_MONTH_NAMES.map((name, i) => ({
      label: name,
      value: i + 1,
    }));
  }, []);

  const yearItems = useMemo(() => {
    const current = todayJalali.year;
    return [current, current + 1, current + 2].map((y) => ({
      label: toPersianDigits(String(y)),
      value: y,
    }));
  }, [todayJalali.year]);

  return (
    <Screen>
      <TopAppBar
        title={kind === "appointment" ? "افزودن ویزیت / برنامه" : "افزودن دارو"}
        showBack
      />

      {/* 5-Step Progress Indicator (Persian RTL) */}
      <View style={styles.progressContainer}>
        <View style={styles.stepBarsRow}>
          {[1, 2, 3, 4, 5].map((sIndex) => {
            const isCompletedOrActive = sIndex <= step;
            return (
              <View
                key={sIndex}
                style={[
                  styles.stepSegment,
                  isCompletedOrActive ? styles.stepSegmentActive : styles.stepSegmentInactive,
                ]}
              />
            );
          })}
        </View>
        <AppText variant="caption" style={styles.stepIndicatorText}>
          {`مرحله ${toPersianDigits(step)} از ۵`}
        </AppText>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ================= STEP 1: Drug Name, Form Factor, Dosage ================= */}
        {step === 1 && (
          <View style={styles.stepBlock}>
            <View style={styles.stepHeader}>
              <AppText variant="title" style={styles.stepTitle}>
                نام و شکل دارویی چیست؟
              </AppText>
              <AppText variant="body" style={styles.stepSubtitle}>
                می‌توانید از لیست داروهای پرکاربرد جستجو کنید یا نام دلخواه بنویسید.
              </AppText>
            </View>

            {/* Drug Search / Input */}
            <View style={styles.fieldWrapper}>
              <TextField
                label="نام دارو"
                placeholder="مثلاً: لوزارتان، کلسیم دی، متفورمین..."
                value={title}
                onChangeText={(val) => {
                  setTitle(val);
                  setSearchQuery(val);
                  setShowDrugSuggestions(val.trim().length > 0);
                }}
              />

              {/* Suggestions Dropdown */}
              {showDrugSuggestions && drugSuggestions.length > 0 && (
                <View style={styles.suggestionsCard}>
                  {drugSuggestions.slice(0, 5).map((item) => (
                    <Pressable
                      key={item.id}
                      style={styles.suggestionRow}
                      onPress={() => selectDrugItem(item)}
                    >
                      <View style={styles.suggestionTextContainer}>
                        <AppText variant="bodyStrong" style={styles.suggestionName}>
                          {item.nameFa}
                        </AppText>
                        <AppText variant="caption" style={styles.suggestionCategory}>
                          {item.nameEn} • {item.categoryFa}
                        </AppText>
                      </View>
                      <View style={styles.suggestionBadge}>
                        <AppText variant="caption" style={styles.suggestionBadgeText}>
                          {DRUG_FORMS.find((f) => f.id === item.defaultForm)?.labelFa ?? "دارو"}
                        </AppText>
                      </View>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>

            {/* Form Factor Selection with Custom Icons */}
            <View style={styles.sectionMargin}>
              <AppText variant="label" style={styles.label}>
                شکل دارویی
              </AppText>
              <View style={styles.formCardsGrid}>
                {DRUG_FORMS.map((form) => {
                  const isSelected = formFactor === form.id;
                  const iconSource = MEDICATION_ICONS[form.id];
                  const displayName =
                    form.id === "injection"
                      ? "آمپول"
                      : form.id === "ointment"
                      ? "پماد"
                      : form.labelFa;

                  return (
                    <Pressable
                      key={form.id}
                      onPress={() => setFormFactor(form.id)}
                      style={[
                        styles.formCard,
                        isSelected ? styles.formCardActive : styles.formCardInactive,
                      ]}
                      accessibilityRole="button"
                      accessibilityState={{ selected: isSelected }}
                    >
                      <View
                        style={[
                          styles.formCardIconWrap,
                          isSelected && styles.formCardIconWrapActive,
                        ]}
                      >
                        <Image
                          source={iconSource}
                          style={styles.formCardImage}
                          resizeMode="contain"
                        />
                      </View>
                      <AppText
                        variant="caption"
                        style={[
                          styles.formCardText,
                          isSelected ? styles.formCardTextActive : styles.formCardTextInactive,
                        ]}
                        numberOfLines={1}
                      >
                        {displayName}
                      </AppText>
                    </Pressable>
                  );
                })}
              </View>
            </View>

            {/* Dosage Input */}
            <View style={styles.sectionMargin}>
              <TextField
                label="مقدار مصرف (دوز)"
                placeholder="مثلاً ۱ عدد، ۵۰ میلی‌گرم، نصف قرص..."
                value={dosage}
                onChangeText={setDosage}
              />
              <View style={styles.quickChipsRow}>
                {["۱ عدد", "۲ عدد", "نصف قرص", "۵۰ میلی‌گرم", "۵ سی‌سی"].map((dChip) => (
                  <Pressable
                    key={dChip}
                    onPress={() => setDosage(dChip)}
                    style={styles.quickChip}
                  >
                    <AppText variant="caption" style={styles.quickChipText}>
                      {dChip}
                    </AppText>
                  </Pressable>
                ))}
              </View>
            </View>
          </View>
        )}

        {/* ================= STEP 2: Reminder Times ================= */}
        {step === 2 && (
          <View style={styles.stepBlock}>
            <View style={styles.stepHeader}>
              <AppText variant="title" style={styles.stepTitle}>
                چه ساعت‌هایی یادت بندازم؟
              </AppText>
              <AppText variant="body" style={styles.stepSubtitle}>
                می‌تونی از ساعت‌های متداول استفاده کنی یا ساعت دلخواهت رو اضافه کنی.
              </AppText>
            </View>

            {/* Active Time Slots */}
            <View style={styles.timeSlotsCard}>
              <AppText variant="label" style={styles.label}>
                نوبت‌های ثبت شده ({toPersianDigits(times.length)} نوبت در روز):
              </AppText>
              {times.length === 0 ? (
                <AppText variant="body" style={styles.emptySlotText}>
                  هنوز ساعتی اضافه نشده است. لطفاً از دکمه زیر ساعت دلخواه اضافه کنید.
                </AppText>
              ) : (
                <View style={styles.timesWrap}>
                  {times.map((slot) => (
                    <View key={slot} style={styles.timeBadge}>
                      <Pressable
                        onPress={() => handleRemoveTimeSlot(slot)}
                        style={styles.timeBadgeDelete}
                        hitSlop={8}
                      >
                        <AppText variant="label" style={styles.deleteCross}>
                          ✕
                        </AppText>
                      </Pressable>
                      <AppText variant="title" style={styles.timeBadgeText}>
                        {toPersianDigits(slot)}
                      </AppText>
                    </View>
                  ))}
                </View>
              )}

              {/* Add Custom Time Button */}
              <Pressable
                onPress={() => setIsTimeModalVisible(true)}
                style={styles.addTimeBtn}
              >
                <AppText variant="bodyStrong" style={styles.addTimeBtnText}>
                  + افزودن ساعت دلخواه
                </AppText>
              </Pressable>
            </View>

            {/* Quick Preset Buttons */}
            <View style={styles.sectionMargin}>
              <AppText variant="label" style={styles.label}>
                ساعت‌های آماده و پیشنهادی
              </AppText>
              <View style={styles.presetRow}>
                {TIME_PRESETS.map((item) => {
                  const isAlreadyAdded = times.includes(item.value);
                  return (
                    <Pressable
                      key={item.value}
                      disabled={isAlreadyAdded}
                      onPress={() => handleAddTimeSlot(item.value)}
                      style={[
                        styles.presetChip,
                        isAlreadyAdded ? styles.presetChipDisabled : styles.presetChipActive,
                      ]}
                    >
                      <AppText
                        variant="caption"
                        style={isAlreadyAdded ? styles.presetTextDisabled : styles.presetTextActive}
                      >
                        {item.label}
                      </AppText>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          </View>
        )}

        {/* ================= STEP 3: Recurrence Frequency ================= */}
        {step === 3 && (
          <View style={styles.stepBlock}>
            <View style={styles.stepHeader}>
              <AppText variant="title" style={styles.stepTitle}>
                چند وقت یک‌بار؟
              </AppText>
              <AppText variant="body" style={styles.stepSubtitle}>
                بیشتر داروها «هر روز» مصرف می‌شوند.
              </AppText>
            </View>

            {/* Radio Option 1: Daily */}
            <Pressable
              onPress={() => setFrequency("daily")}
              style={[
                styles.recurrenceOptionCard,
                frequency === "daily" && styles.recurrenceOptionCardActive,
              ]}
            >
              <View style={styles.optionRadioCircle}>
                {frequency === "daily" && <View style={styles.optionRadioInner} />}
              </View>
              <View style={styles.optionTextContainer}>
                <AppText variant="bodyStrong" style={styles.optionTitle}>
                  هر روز
                </AppText>
                <AppText variant="caption" style={styles.optionDesc}>
                  دارو هر روز در ساعت‌های مشخص شده یادآوری می‌شود.
                </AppText>
              </View>
            </Pressable>

            {/* Radio Option 2: Specific Weekdays */}
            <Pressable
              onPress={() => setFrequency("specific_days")}
              style={[
                styles.recurrenceOptionCard,
                frequency === "specific_days" && styles.recurrenceOptionCardActive,
              ]}
            >
              <View style={styles.optionRadioCircle}>
                {frequency === "specific_days" && <View style={styles.optionRadioInner} />}
              </View>
              <View style={styles.optionTextContainer}>
                <AppText variant="bodyStrong" style={styles.optionTitle}>
                  روزهای خاص هفته
                </AppText>
                <AppText variant="caption" style={styles.optionDesc}>
                  مثلاً شنبه، دوشنبه، چهارشنبه
                </AppText>
              </View>
            </Pressable>

            {/* Weekdays Selector Sub-view */}
            {frequency === "specific_days" && (
              <View style={styles.weekdaysSubCard}>
                <AppText variant="caption" style={styles.subCardLabel}>
                  روزهای مصرف را لمس و انتخاب کنید:
                </AppText>
                <View style={styles.weekdaysWrap}>
                  {JALALI_WEEKDAYS.map((day) => {
                    const isSelected = selectedWeekdays.includes(day.code);
                    return (
                      <Pressable
                        key={day.code}
                        onPress={() => toggleWeekday(day.code)}
                        style={[
                          styles.weekdayPill,
                          isSelected ? styles.weekdayPillActive : styles.weekdayPillInactive,
                        ]}
                      >
                        <AppText
                          variant="caption"
                          style={isSelected ? styles.weekdayTextActive : styles.weekdayTextInactive}
                        >
                          {day.label}
                        </AppText>
                      </Pressable>
                    );
                  })}
                </View>
              </View>
            )}

            {/* Radio Option 3: Every N Days */}
            <Pressable
              onPress={() => setFrequency("every_n_days")}
              style={[
                styles.recurrenceOptionCard,
                frequency === "every_n_days" && styles.recurrenceOptionCardActive,
              ]}
            >
              <View style={styles.optionRadioCircle}>
                {frequency === "every_n_days" && <View style={styles.optionRadioInner} />}
              </View>
              <View style={styles.optionTextContainer}>
                <AppText variant="bodyStrong" style={styles.optionTitle}>
                  دوره‌ای (هر چند روز یک‌بار)
                </AppText>
                <AppText variant="caption" style={styles.optionDesc}>
                  مثلاً هر ۲ روز یا هر ۷ روز یک نوبت
                </AppText>
              </View>
            </Pressable>

            {/* Interval Sub-view */}
            {frequency === "every_n_days" && (
              <View style={styles.weekdaysSubCard}>
                <AppText variant="caption" style={styles.subCardLabel}>
                  فاصله بین هر نوبت:
                </AppText>
                <View style={styles.intervalRow}>
                  {["۲", "۳", "۴", "۷"].map((n) => (
                    <Pressable
                      key={n}
                      onPress={() => setEveryNDays(n)}
                      style={[
                        styles.intervalPill,
                        everyNDays === n ? styles.intervalPillActive : styles.intervalPillInactive,
                      ]}
                    >
                      <AppText
                        variant="body"
                        style={everyNDays === n ? styles.intervalTextActive : styles.intervalTextInactive}
                      >
                        {`هر ${toPersianDigits(n)} روز`}
                      </AppText>
                    </Pressable>
                  ))}
                </View>
              </View>
            )}

            {/* Radio Option 4: Once */}
            <Pressable
              onPress={() => setFrequency("once")}
              style={[
                styles.recurrenceOptionCard,
                frequency === "once" && styles.recurrenceOptionCardActive,
              ]}
            >
              <View style={styles.optionRadioCircle}>
                {frequency === "once" && <View style={styles.optionRadioInner} />}
              </View>
              <View style={styles.optionTextContainer}>
                <AppText variant="bodyStrong" style={styles.optionTitle}>
                  یک نوبت (فقط یک‌بار)
                </AppText>
                <AppText variant="caption" style={styles.optionDesc}>
                  مناسب برای نوبت ویزیت پزشک یا داروی تک‌دوز
                </AppText>
              </View>
            </Pressable>
          </View>
        )}

        {/* ================= STEP 4: Start Date & Duration ================= */}
        {step === 4 && (
          <View style={styles.stepBlock}>
            <View style={styles.stepHeader}>
              <AppText variant="title" style={styles.stepTitle}>
                از چه تاریخی شروع می‌کنی؟
              </AppText>
              <AppText variant="body" style={styles.stepSubtitle}>
                معمولاً از همین امروز است.
              </AppText>
            </View>

            {/* Today Button & Date Display */}
            <View style={styles.dateSelectorCard}>
              <View style={styles.dateHeaderRow}>
                <AppText variant="title" style={styles.currentDateDisplay}>
                  {`تاریخ شروع: ${toPersianDigits(startDateFormatted)}`}
                </AppText>
                <Pressable onPress={handleSetToday} style={styles.todayShortcutBtn}>
                  <AppText variant="bodyStrong" style={styles.todayShortcutText}>
                    امروز
                  </AppText>
                </Pressable>
              </View>

              {/* Shamsi Wheel Picker Section */}
              <View style={styles.dateWheelsContainer}>
                {/* Year */}
                <View style={styles.wheelCol}>
                  <AppText variant="caption" style={styles.wheelColLabel}>
                    سال
                  </AppText>
                  <WheelPicker
                    items={yearItems}
                    selectedValue={startYear}
                    onValueChange={(val) => setStartYear(Number(val))}
                    width={85}
                  />
                </View>

                {/* Month */}
                <View style={styles.wheelCol}>
                  <AppText variant="caption" style={styles.wheelColLabel}>
                    ماه
                  </AppText>
                  <WheelPicker
                    items={monthItems}
                    selectedValue={startMonth}
                    onValueChange={(val) => setStartMonth(Number(val))}
                    width={100}
                  />
                </View>

                {/* Day */}
                <View style={styles.wheelCol}>
                  <AppText variant="caption" style={styles.wheelColLabel}>
                    روز
                  </AppText>
                  <WheelPicker
                    items={daysItems}
                    selectedValue={startDay}
                    onValueChange={(val) => setStartDay(Number(val))}
                    width={80}
                  />
                </View>
              </View>
            </View>

            {/* Treatment Duration Section */}
            <View style={styles.sectionMargin}>
              <AppText variant="title" style={styles.stepTitle}>
                تا کی ادامه دارد؟
              </AppText>
              <AppText variant="body" style={styles.stepSubtitle}>
                مدت زمان مصرف این دارو را تعیین کنید.
              </AppText>

              <View style={styles.durationChipsRow}>
                {[
                  { id: "ongoing", label: "همیشگی" },
                  { id: "7_days", label: "۷ روز" },
                  { id: "14_days", label: "۱۴ روز" },
                  { id: "30_days", label: "۳۰ روز" },
                ].map((item) => {
                  const isSelected = durationOption === item.id;
                  return (
                    <Pressable
                      key={item.id}
                      onPress={() => setDurationOption(item.id as DurationOption)}
                      style={[
                        styles.durationPill,
                        isSelected ? styles.durationPillActive : styles.durationPillInactive,
                      ]}
                    >
                      <AppText
                        variant="body"
                        style={isSelected ? styles.durationTextActive : styles.durationTextInactive}
                      >
                        {item.label}
                      </AppText>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          </View>
        )}

        {/* ================= STEP 5: Food Instructions & Review ================= */}
        {step === 5 && (
          <View style={styles.stepBlock}>
            <View style={styles.stepHeader}>
              <AppText variant="title" style={styles.stepTitle}>
                دستور مصرف و تایید نهایی
              </AppText>
              <AppText variant="body" style={styles.stepSubtitle}>
                دارو همراه با غذا میل شود یا با معده خالی؟
              </AppText>
            </View>

            {/* Meal Timing Chips */}
            <View style={styles.mealChipsGrid}>
              {MEAL_INSTRUCTIONS.map((instr) => {
                const isSelected = selectedMealInstruction === instr;
                return (
                  <Pressable
                    key={instr}
                    onPress={() => setSelectedMealInstruction(instr)}
                    style={[
                      styles.mealChip,
                      isSelected ? styles.mealChipActive : styles.mealChipInactive,
                    ]}
                  >
                    <AppText
                      variant="body"
                      style={isSelected ? styles.mealChipTextActive : styles.mealChipTextInactive}
                    >
                      {instr}
                    </AppText>
                  </Pressable>
                );
              })}
            </View>

            {/* Additional Notes */}
            <View style={styles.sectionMargin}>
              <TextField
                label="توضیح اضافه یا هشدار خاص (اختیاری)"
                placeholder="مثلاً: همراه با یک لیوان آب کامل میل شود"
                value={additionalNote}
                onChangeText={setAdditionalNote}
              />
            </View>

            {/* Summary Review Card */}
            <Card style={styles.summaryCard}>
              <View style={styles.summaryHeader}>
                <View style={styles.summaryTitleCol}>
                  <AppText variant="title" style={styles.summaryTitle}>
                    {title}
                  </AppText>
                  <View style={styles.summaryBadgeRow}>
                    <View style={styles.summaryFormBadge}>
                      <AppText variant="caption" style={styles.summaryFormBadgeText}>
                        {DRUG_FORMS.find((f) => f.id === formFactor)?.labelFa ?? "دارو"}
                      </AppText>
                    </View>
                  </View>
                </View>

                {/* Medication Icon Illustration */}
                <View style={styles.summaryIconContainer}>
                  <Image
                    source={MEDICATION_ICONS[formFactor]}
                    style={styles.summaryMedicationImage}
                    resizeMode="contain"
                  />
                </View>
              </View>

              <View style={styles.summaryDivider} />

              <View style={styles.summaryRow}>
                <AppText variant="caption" style={styles.summaryLabel}>
                  مقدار دوز:
                </AppText>
                <AppText variant="body" style={styles.summaryValue}>
                  {dosage || "طبق دستور پزشک"}
                </AppText>
              </View>

              <View style={styles.summaryRow}>
                <AppText variant="caption" style={styles.summaryLabel}>
                  ساعت‌های یادآوری:
                </AppText>
                <AppText variant="body" style={styles.summaryValue}>
                  {times.map(toPersianDigits).join(" ، ")}
                </AppText>
              </View>

              <View style={styles.summaryRow}>
                <AppText variant="caption" style={styles.summaryLabel}>
                  تکرار و تداوم:
                </AppText>
                <AppText variant="body" style={styles.summaryValue}>
                  {frequency === "daily"
                    ? "هر روز"
                    : frequency === "specific_days"
                    ? `روزهای ${selectedWeekdays.map((c) => JALALI_WEEKDAYS.find((w) => w.code === c)?.label).join("، ")}`
                    : frequency === "every_n_days"
                    ? `هر ${toPersianDigits(everyNDays)} روز`
                    : "یک نوبت"}
                  {" • "}
                  {durationOption === "ongoing"
                    ? "همیشگی"
                    : durationOption === "7_days"
                    ? "به مدت ۷ روز"
                    : durationOption === "14_days"
                    ? "به مدت ۱۴ روز"
                    : "به مدت ۳۰ روز"}
                </AppText>
              </View>

              <View style={styles.summaryRow}>
                <AppText variant="caption" style={styles.summaryLabel}>
                  دستور مصرف:
                </AppText>
                <AppText variant="body" style={styles.summaryValue}>
                  {selectedMealInstruction}
                </AppText>
              </View>
            </Card>
          </View>
        )}

        {/* Inline Error Notice */}
        {error && (
          <View style={styles.errorBox}>
            <AppText variant="body" style={styles.errorText}>
              {error}
            </AppText>
          </View>
        )}
      </ScrollView>

      {/* Sticky Bottom Navigation Buttons */}
      <View style={styles.bottomNavContainer}>
        <Button
          label={step === 5 ? (loading ? "در حال ذخیره..." : "ثبت نهایی دارو") : "مرحله بعد"}
          variant="primary"
          loading={loading}
          onPress={handleNext}
          style={styles.navNextBtn}
        />
        {step > 1 && (
          <Button
            label="مرحله قبل"
            variant="secondary"
            onPress={handlePrev}
            style={styles.navPrevBtn}
          />
        )}
      </View>

      {/* Time Picker Modal (Tumbler / Wheel) */}
      <Modal
        visible={isTimeModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setIsTimeModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <AppText variant="title" style={styles.modalTitle}>
              ساعت مصرف
            </AppText>

            <View style={styles.timeWheelRow}>
              {/* Hour Wheel */}
              <View style={styles.timeWheelCol}>
                <AppText variant="caption" style={styles.timeWheelLabel}>
                  ساعت
                </AppText>
                <WheelPicker
                  items={HOURS}
                  selectedValue={pickerHour}
                  onValueChange={(val) => setPickerHour(Number(val))}
                  width={90}
                />
              </View>

              <AppText variant="time" style={styles.timeColon}>
                :
              </AppText>

              {/* Minute Wheel */}
              <View style={styles.timeWheelCol}>
                <AppText variant="caption" style={styles.timeWheelLabel}>
                  دقیقه
                </AppText>
                <WheelPicker
                  items={MINUTES}
                  selectedValue={pickerMinute}
                  onValueChange={(val) => setPickerMinute(Number(val))}
                  width={90}
                />
              </View>
            </View>

            <View style={styles.modalButtonsRow}>
              <Button
                label="تایید"
                variant="primary"
                onPress={handleConfirmTimeModal}
                style={styles.modalConfirmBtn}
              />
              <Button
                label="انصراف"
                variant="ghost"
                onPress={() => setIsTimeModalVisible(false)}
                style={styles.modalCancelBtn}
              />
            </View>
          </View>
        </View>
      </Modal>
    </Screen>
  );
}

const styles = StyleSheet.create({
  progressContainer: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xs,
  },
  stepBarsRow: {
    flexDirection: "row-reverse",
    gap: 6,
    marginBottom: spacing.xs,
  },
  stepSegment: {
    flex: 1,
    height: 4,
    borderRadius: 2,
  },
  stepSegmentActive: {
    backgroundColor: colors.primary,
  },
  stepSegmentInactive: {
    backgroundColor: colors.borderMuted,
  },
  stepIndicatorText: {
    textAlign: "right",
    color: colors.textSecondary,
    writingDirection: "rtl",
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
    paddingBottom: 110,
    gap: spacing.md,
  },
  stepBlock: {
    gap: spacing.md,
    width: "100%",
  },
  stepHeader: {
    marginTop: spacing.xs,
    gap: 4,
    alignItems: "flex-end",
    width: "100%",
  },
  stepTitle: {
    color: colors.text,
    textAlign: "right",
    width: "100%",
    writingDirection: "rtl",
  },
  stepSubtitle: {
    color: colors.textSecondary,
    textAlign: "right",
    width: "100%",
    writingDirection: "rtl",
    lineHeight: 20,
  },
  fieldWrapper: {
    position: "relative",
    width: "100%",
  },
  suggestionsCard: {
    position: "absolute",
    top: 72,
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.borderMuted,
    elevation: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    zIndex: 100,
  },
  suggestionRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderMuted,
  },
  suggestionTextContainer: {
    alignItems: "flex-end",
    flex: 1,
  },
  suggestionName: {
    color: colors.text,
    textAlign: "right",
    writingDirection: "rtl",
  },
  suggestionCategory: {
    color: colors.textSecondary,
    textAlign: "right",
    writingDirection: "rtl",
  },
  suggestionBadge: {
    backgroundColor: "rgba(0, 104, 95, 0.1)",
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  suggestionBadgeText: {
    color: colors.primary,
    textAlign: "right",
  },
  sectionMargin: {
    gap: spacing.xs,
    width: "100%",
    alignItems: "flex-end",
  },
  label: {
    color: colors.text,
    marginBottom: 4,
    textAlign: "right",
    width: "100%",
    writingDirection: "rtl",
  },
  formCardsGrid: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8,
    width: "100%",
    justifyContent: "space-between",
  },
  formCard: {
    width: "22.8%",
    minHeight: 88,
    borderRadius: radius.md,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.xs,
    paddingHorizontal: 2,
  },
  formCardActive: {
    backgroundColor: "rgba(0, 104, 95, 0.08)",
    borderColor: colors.primary,
  },
  formCardInactive: {
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
  },
  formCardIconWrap: {
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  formCardIconWrapActive: {
    transform: [{ scale: 1.08 }],
  },
  formCardImage: {
    width: 40,
    height: 40,
  },
  formCardText: {
    textAlign: "center",
    fontSize: 12,
    writingDirection: "rtl",
  },
  formCardTextActive: {
    color: colors.primary,
    fontWeight: "700",
  },
  formCardTextInactive: {
    color: colors.textSecondary,
    fontWeight: "500",
  },
  quickChipsRow: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 6,
    marginTop: spacing.xs,
    width: "100%",
    justifyContent: "flex-start",
  },
  quickChip: {
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.sm,
  },
  quickChipText: {
    color: colors.textSecondary,
    textAlign: "right",
    writingDirection: "rtl",
  },
  timeSlotsCard: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.borderMuted,
    gap: spacing.md,
    width: "100%",
    alignItems: "flex-end",
  },
  emptySlotText: {
    color: colors.textSecondary,
    textAlign: "right",
    paddingVertical: spacing.sm,
    width: "100%",
    writingDirection: "rtl",
  },
  timesWrap: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: spacing.sm,
    width: "100%",
    justifyContent: "flex-start",
  },
  timeBadge: {
    flexDirection: "row-reverse",
    alignItems: "center",
    backgroundColor: "rgba(0, 104, 95, 0.08)",
    borderWidth: 1,
    borderColor: "rgba(0, 104, 95, 0.25)",
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    gap: spacing.sm,
  },
  timeBadgeText: {
    color: colors.primary,
  },
  timeBadgeDelete: {
    padding: 2,
  },
  deleteCross: {
    color: colors.error,
    fontSize: 14,
  },
  addTimeBtn: {
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.sm,
    borderWidth: 1,
    borderColor: colors.primary,
    borderStyle: "dashed",
    borderRadius: radius.md,
  },
  addTimeBtnText: {
    color: colors.primary,
  },
  presetRow: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: spacing.xs,
    width: "100%",
    justifyContent: "flex-start",
  },
  presetChip: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.sm,
    borderWidth: 1,
  },
  presetChipActive: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.borderMuted,
  },
  presetChipDisabled: {
    backgroundColor: "rgba(0, 104, 95, 0.08)",
    borderColor: "rgba(0, 104, 95, 0.2)",
    opacity: 0.6,
  },
  presetTextActive: {
    color: colors.text,
    textAlign: "right",
    writingDirection: "rtl",
  },
  presetTextDisabled: {
    color: colors.primary,
    textAlign: "right",
    writingDirection: "rtl",
  },
  recurrenceOptionCard: {
    flexDirection: "row-reverse",
    alignItems: "center",
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1.5,
    borderColor: colors.borderMuted,
    gap: spacing.md,
    width: "100%",
  },
  recurrenceOptionCardActive: {
    borderColor: colors.primary,
    backgroundColor: "rgba(0, 104, 95, 0.04)",
  },
  optionRadioCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: colors.primary,
    justifyContent: "center",
    alignItems: "center",
  },
  optionRadioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.primary,
  },
  optionTextContainer: {
    flex: 1,
    alignItems: "flex-end",
    gap: 2,
  },
  optionTitle: {
    color: colors.text,
    textAlign: "right",
    width: "100%",
    writingDirection: "rtl",
  },
  optionDesc: {
    color: colors.textSecondary,
    textAlign: "right",
    width: "100%",
    writingDirection: "rtl",
  },
  weekdaysSubCard: {
    backgroundColor: colors.surfaceMuted,
    padding: spacing.md,
    borderRadius: radius.md,
    gap: spacing.sm,
    width: "100%",
    alignItems: "flex-end",
  },
  subCardLabel: {
    color: colors.textSecondary,
    textAlign: "right",
    width: "100%",
    writingDirection: "rtl",
  },
  weekdaysWrap: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: spacing.xs,
    width: "100%",
    justifyContent: "flex-start",
  },
  weekdayPill: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.sm,
    borderWidth: 1,
  },
  weekdayPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  weekdayPillInactive: {
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
  },
  weekdayTextActive: {
    color: colors.primaryOn,
    textAlign: "center",
  },
  weekdayTextInactive: {
    color: colors.textSecondary,
    textAlign: "center",
  },
  intervalRow: {
    flexDirection: "row-reverse",
    gap: spacing.xs,
    width: "100%",
  },
  intervalPill: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: "center",
    borderRadius: radius.md,
    borderWidth: 1,
  },
  intervalPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  intervalPillInactive: {
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
  },
  intervalTextActive: {
    color: colors.primaryOn,
    textAlign: "center",
  },
  intervalTextInactive: {
    color: colors.textSecondary,
    textAlign: "center",
  },
  dateSelectorCard: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.borderMuted,
    gap: spacing.md,
    width: "100%",
  },
  dateHeaderRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    width: "100%",
  },
  todayShortcutBtn: {
    backgroundColor: "rgba(0, 104, 95, 0.12)",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.sm,
  },
  todayShortcutText: {
    color: colors.primary,
  },
  currentDateDisplay: {
    color: colors.text,
    textAlign: "right",
    writingDirection: "rtl",
  },
  dateWheelsContainer: {
    flexDirection: "row-reverse",
    justifyContent: "center",
    gap: spacing.md,
    paddingVertical: spacing.xs,
  },
  wheelCol: {
    alignItems: "center",
    gap: 4,
  },
  wheelColLabel: {
    color: colors.textSecondary,
    textAlign: "center",
  },
  durationChipsRow: {
    flexDirection: "row-reverse",
    gap: spacing.xs,
    marginTop: spacing.xs,
    width: "100%",
  },
  durationPill: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: "center",
    borderRadius: radius.md,
    borderWidth: 1,
  },
  durationPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  durationPillInactive: {
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
  },
  durationTextActive: {
    color: colors.primaryOn,
    textAlign: "center",
  },
  durationTextInactive: {
    color: colors.textSecondary,
    textAlign: "center",
  },
  mealChipsGrid: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: spacing.xs,
    width: "100%",
    justifyContent: "flex-start",
  },
  mealChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  mealChipActive: {
    backgroundColor: "rgba(0, 104, 95, 0.12)",
    borderColor: colors.primary,
  },
  mealChipInactive: {
    backgroundColor: colors.surface,
    borderColor: colors.borderMuted,
  },
  mealChipTextActive: {
    color: colors.primary,
    textAlign: "right",
    writingDirection: "rtl",
  },
  mealChipTextInactive: {
    color: colors.textSecondary,
    textAlign: "right",
    writingDirection: "rtl",
  },
  summaryCard: {
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderMuted,
    borderRadius: radius.lg,
    gap: spacing.sm,
    width: "100%",
  },
  summaryHeader: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    width: "100%",
  },
  summaryTitleCol: {
    alignItems: "flex-end",
    flex: 1,
    gap: 4,
  },
  summaryTitle: {
    color: colors.text,
    textAlign: "right",
    writingDirection: "rtl",
  },
  summaryBadgeRow: {
    flexDirection: "row-reverse",
  },
  summaryIconContainer: {
    width: 52,
    height: 52,
    borderRadius: radius.md,
    backgroundColor: "rgba(0, 104, 95, 0.06)",
    alignItems: "center",
    justifyContent: "center",
    marginLeft: spacing.sm,
  },
  summaryMedicationImage: {
    width: 44,
    height: 44,
  },
  summaryFormBadge: {
    backgroundColor: "rgba(0, 104, 95, 0.1)",
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  summaryFormBadgeText: {
    color: colors.primary,
    textAlign: "right",
  },
  summaryDivider: {
    height: 1,
    backgroundColor: colors.borderMuted,
    width: "100%",
  },
  summaryRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    width: "100%",
  },
  summaryLabel: {
    color: colors.textSecondary,
    textAlign: "right",
    writingDirection: "rtl",
  },
  summaryValue: {
    color: colors.text,
    textAlign: "right",
    writingDirection: "rtl",
  },
  errorBox: {
    backgroundColor: "rgba(186, 26, 26, 0.08)",
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: "rgba(186, 26, 26, 0.2)",
    width: "100%",
  },
  errorText: {
    color: colors.error,
    textAlign: "right",
    writingDirection: "rtl",
  },
  bottomNavContainer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row-reverse",
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.borderMuted,
    gap: spacing.md,
  },
  navPrevBtn: {
    flex: 1,
  },
  navNextBtn: {
    flex: 2,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: spacing.lg,
  },
  modalCard: {
    width: "100%",
    maxWidth: 320,
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: spacing.lg,
    alignItems: "center",
    gap: spacing.md,
  },
  modalTitle: {
    color: colors.text,
    textAlign: "center",
  },
  timeWheelRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: spacing.md,
  },
  timeWheelCol: {
    alignItems: "center",
    gap: 4,
  },
  timeWheelLabel: {
    color: colors.textSecondary,
    textAlign: "center",
  },
  timeColon: {
    color: colors.primary,
    marginTop: 18,
  },
  modalButtonsRow: {
    flexDirection: "row-reverse",
    width: "100%",
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  modalConfirmBtn: {
    flex: 1,
  },
  modalCancelBtn: {
    flex: 1,
  },
});
