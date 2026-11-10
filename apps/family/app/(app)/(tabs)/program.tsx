import { useMemo, useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../src/api/queryKeys";
import { getAppErrorDisplay } from "../../../src/api/errors";
import { listCareActivities, listCompletions, listPrescriptions } from "../../../src/api/endpoints/care";
import { listOccurrences } from "../../../src/api/endpoints/scheduling";
import { endOfLocalDay, startOfLocalDay } from "../../../src/i18n/dates";
import {
  t,
  formatClock,
  formatPersianDate,
  careActivityStatusLabel,
  completionStateLabel,
  occurrenceStatusLabel,
} from "../../../src/i18n";
import {
  formatJalaliMonthYear,
  getJalaliMonthGrid,
  getJalaliWeekDays,
  getTodayJalali,
  gregorianToJalali,
  JALALI_MONTH_NAMES,
  JALALI_WEEKDAYS,
} from "../../../src/services/program/jalali";
import { toPersianDigits } from "../../../src/i18n/numerals";
import { colors, radius, spacing } from "../../../src/theme/tokens";
import {
  AppText,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Screen,
  SetupActions,
  TopAppBar,
} from "../../../src/components";
import { Icon } from "../../../src/components/Icon";
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { syncProgramAlarms } from "../../../src/services/medication/alarmScheduler";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { visualKindFor } from "../../../src/services/program/activityKind";
import { shouldShowOnTodayProgram } from "../../../src/services/program/todayProgram";
import type { CareActivity, CareCompletion, Occurrence, Prescription } from "../../../src/api/types";

type ProgramTab = "today" | "week" | "calendar";

interface ProgramItem {
  activity: CareActivity;
  occurrence: Occurrence;
  prescription?: Prescription;
  completion?: CareCompletion;
  jalaliDateStr: string;
}

export default function ProgramScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();

  const [activeTab, setActiveTab] = useState<ProgramTab>("today");
  const [weekOffset, setWeekOffset] = useState(0);

  const todayJalali = useMemo(() => getTodayJalali(), []);
  const [calYear, setCalYear] = useState(todayJalali.year);
  const [calMonth, setCalMonth] = useState(todayJalali.month);
  const [selectedDateStr, setSelectedDateStr] = useState(todayJalali.formatted);

  const weekDays = useMemo(() => getJalaliWeekDays(new Date(), weekOffset), [weekOffset]);
  const monthGrid = useMemo(() => getJalaliMonthGrid(calYear, calMonth), [calYear, calMonth]);

  // Compute active date window for occurrences query
  const { queryStart, queryEnd } = useMemo(() => {
    if (activeTab === "today") {
      return {
        queryStart: startOfLocalDay().toISOString(),
        queryEnd: endOfLocalDay().toISOString(),
      };
    }
    if (activeTab === "week") {
      const first = weekDays[0].date;
      const last = weekDays[6].date;
      return {
        queryStart: new Date(first.getFullYear(), first.getMonth(), first.getDate(), 0, 0, 0).toISOString(),
        queryEnd: new Date(last.getFullYear(), last.getMonth(), last.getDate(), 23, 59, 59).toISOString(),
      };
    }
    // calendar
    const firstCell = monthGrid[0][0].date;
    const lastRow = monthGrid[monthGrid.length - 1];
    const lastCell = lastRow[lastRow.length - 1].date;
    return {
      queryStart: new Date(firstCell.getFullYear(), firstCell.getMonth(), firstCell.getDate(), 0, 0, 0).toISOString(),
      queryEnd: new Date(lastCell.getFullYear(), lastCell.getMonth(), lastCell.getDate(), 23, 59, 59).toISOString(),
    };
  }, [activeTab, weekDays, monthGrid]);

  const query = useQuery({
    queryKey: elderId
      ? [...queryKeys.careActivities(elderId), "program", activeTab, queryStart, queryEnd]
      : ["program"],
    enabled: Boolean(elderId),
    queryFn: async () => {
      const [activities, prescriptions] = await Promise.all([
        listCareActivities(elderId as string).catch(() => [] as CareActivity[]),
        listPrescriptions(elderId as string).catch(() => [] as Prescription[]),
      ]);

      const items: ProgramItem[] = [];
      await Promise.all(
        activities.map(async (activity) => {
          const [occ, history] = await Promise.all([
            listOccurrences(activity.schedule_definition_id, {
              type: "between",
              start: queryStart,
              end: queryEnd,
            }).catch(() => [] as Occurrence[]),
            listCompletions(activity.id).catch(() => [] as CareCompletion[]),
          ]);
          const list = Array.isArray(occ) ? occ : occ ? [occ] : [];
          for (const occurrence of list) {
            const occDate = new Date(occurrence.scheduled_for);
            const [jy, jm, jd] = gregorianToJalali(
              occDate.getFullYear(),
              occDate.getMonth() + 1,
              occDate.getDate(),
            );
            const pad2 = (n: number) => String(n).padStart(2, "0");
            const jDateStr = `${jy}/${pad2(jm)}/${pad2(jd)}`;

            if (activeTab === "today" && !shouldShowOnTodayProgram(activity, occurrence)) {
              continue;
            }
            items.push({
              activity,
              occurrence,
              prescription: prescriptions.find((p) => p.care_activity_id === activity.id),
              completion: history.find((c) => c.occurrence_id === occurrence.id),
              jalaliDateStr: jDateStr,
            });
          }
        }),
      );

      items.sort(
        (a, b) =>
          new Date(a.occurrence.scheduled_for).getTime() - new Date(b.occurrence.scheduled_for).getTime(),
      );

      if (activeTab === "today") {
        void syncProgramAlarms(items);
      }
      return { activities, items };
    },
  });

  // Group items by Jalali date string
  const itemsByDay = useMemo(() => {
    const map: Record<string, ProgramItem[]> = {};
    for (const item of query.data?.items ?? []) {
      if (!map[item.jalaliDateStr]) {
        map[item.jalaliDateStr] = [];
      }
      map[item.jalaliDateStr].push(item);
    }
    return map;
  }, [query.data?.items]);

  if (!elderId) {
    return (
      <Screen>
        <TopAppBar title={t.programTitle} />
        <EmptyState
          title={t.noElderTitle}
          body={t.noElderBody}
          actionLabel={t.setupElder}
          onAction={() => router.push("/(auth)/create-elder")}
        />
      </Screen>
    );
  }

  if (query.isPending) {
    return (
      <Screen>
        <TopAppBar title={t.programTitle} />
        <LoadingSkeleton />
      </Screen>
    );
  }
  if (query.isError) {
    const errorDisplay = getAppErrorDisplay(query.error);
    return (
      <Screen>
        <TopAppBar title={t.programTitle} />
        <ErrorState
          title={errorDisplay.title}
          body={errorDisplay.body}
          onRetry={() => void query.refetch()}
        />
      </Screen>
    );
  }

  const data = query.data;
  const setupRequired = !data?.activities.length;
  const todayItems = data?.items ?? [];
  const selectedDayItems = itemsByDay[selectedDateStr] ?? [];

  function renderProgramCard(item: ProgramItem) {
    const kind = visualKindFor(item.activity.activity_type, item.activity.display_title);
    return (
      <Pressable
        key={item.occurrence.id}
        onPress={() => {
          if (kind === "medication" && (item.occurrence.status === "DUE" || !item.completion)) {
            router.push({
              pathname: "/(app)/program/reminder",
              params: {
                medicationTitle: item.activity.display_title,
                dosage: item.prescription?.dosage_information || item.activity.display_subtitle || "",
                timeLabel: formatClock(item.occurrence.scheduled_for),
                instructions: item.prescription?.elder_friendly_description || "",
                occurrenceId: item.occurrence.id,
                activityId: item.activity.id,
              },
            });
          } else {
            router.push(`/(app)/program/${item.activity.id}`);
          }
        }}
      >
        <Card accent={kind === "medication" ? "medication" : kind === "appointment" ? "info" : "none"}>
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <AppText variant="label">{item.activity.display_title}</AppText>
              <AppText variant="body" color={colors.textSecondary}>
                {item.prescription?.elder_friendly_description || item.activity.display_subtitle}
              </AppText>
              <AppText variant="caption" color={colors.textMuted}>
                {item.completion
                  ? completionStateLabel(item.completion.completion_state)
                  : item.occurrence.status === "DUE"
                    ? t.waitingForConfirmation
                    : item.activity.status !== "ACTIVE"
                      ? careActivityStatusLabel(item.activity.status)
                      : occurrenceStatusLabel(item.occurrence.status)}
              </AppText>
            </View>
            <AppText variant="time">{formatClock(item.occurrence.scheduled_for)}</AppText>
          </View>
        </Card>
      </Pressable>
    );
  }

  return (
    <Screen>
      <TopAppBar title={t.programTitle} />

      {/* Tabs Switcher */}
      <View style={styles.tabs}>
        <Pressable
          style={[styles.tab, activeTab === "today" && styles.tabActive]}
          onPress={() => {
            setActiveTab("today");
            setSelectedDateStr(todayJalali.formatted);
          }}
        >
          <AppText
            variant="label"
            color={activeTab === "today" ? colors.primary : colors.textSecondary}
            align="center"
          >
            {t.today}
          </AppText>
        </Pressable>

        <Pressable
          style={[styles.tab, activeTab === "week" && styles.tabActive]}
          onPress={() => {
            setActiveTab("week");
            setSelectedDateStr(todayJalali.formatted);
          }}
        >
          <AppText
            variant="label"
            color={activeTab === "week" ? colors.primary : colors.textSecondary}
            align="center"
          >
            {t.week}
          </AppText>
        </Pressable>

        <Pressable
          style={[styles.tab, activeTab === "calendar" && styles.tabActive]}
          onPress={() => {
            setActiveTab("calendar");
            setSelectedDateStr(todayJalali.formatted);
          }}
        >
          <AppText
            variant="label"
            color={activeTab === "calendar" ? colors.primary : colors.textSecondary}
            align="center"
          >
            {t.calendar}
          </AppText>
        </Pressable>
      </View>

      {/* TAB 1: TODAY */}
      {activeTab === "today" ? (
        <>
          <AppText variant="title">{formatPersianDate(new Date())}</AppText>
          <AppText variant="caption" color={colors.textMuted}>
            {t.today}
          </AppText>

          {setupRequired ? (
            <>
              <EmptyState title={t.firstSetupTitle} body={t.firstSetupBody} />
              <SetupActions
                onAddMedication={() => router.push("/(app)/program/add?kind=medication")}
                onAddAppointment={() => router.push("/(app)/program/add?kind=appointment")}
                onConnectDevice={() => router.push("/(app)/(tabs)/devices")}
              />
            </>
          ) : !todayItems.length ? (
            <EmptyState title={t.empty} body={t.emptyTodayProgram} />
          ) : (
            todayItems.map(renderProgramCard)
          )}
        </>
      ) : null}

      {/* TAB 2: WEEK */}
      {activeTab === "week" ? (
        <View style={styles.tabContent}>
          {/* Week Navigation Header */}
          <View style={styles.navRow}>
            <Pressable
              style={styles.navButton}
              onPress={() => setWeekOffset((w) => w - 1)}
              accessibilityLabel="هفته قبل"
            >
              <AppText variant="label" color={colors.primary}>
                {"‹ هفته قبل"}
              </AppText>
            </Pressable>

            <View style={styles.navCenter}>
              <AppText variant="label" align="center">
                {toPersianDigits(
                  `${weekDays[0].jalaliDay} ${JALALI_MONTH_NAMES[weekDays[0].jalaliMonth - 1]} تا ${weekDays[6].jalaliDay} ${JALALI_MONTH_NAMES[weekDays[6].jalaliMonth - 1]}`,
                )}
              </AppText>
              {weekOffset !== 0 ? (
                <Pressable
                  style={styles.todayPill}
                  onPress={() => {
                    setWeekOffset(0);
                    setSelectedDateStr(todayJalali.formatted);
                  }}
                >
                  <AppText variant="caption" color={colors.primary}>
                    {t.today}
                  </AppText>
                </Pressable>
              ) : null}
            </View>

            <Pressable
              style={styles.navButton}
              onPress={() => setWeekOffset((w) => w + 1)}
              accessibilityLabel="هفته بعد"
            >
              <AppText variant="label" color={colors.primary}>
                {"هفته بعد ›"}
              </AppText>
            </Pressable>
          </View>

          {/* 7-Day Strip */}
          <View style={styles.weekStrip}>
            {weekDays.map((day) => {
              const isSelected = selectedDateStr === day.jalaliDateStr;
              const hasMedication = Boolean(itemsByDay[day.jalaliDateStr]?.length);
              return (
                <Pressable
                  key={day.jalaliDateStr}
                  style={[
                    styles.weekDayCell,
                    isSelected && styles.weekDayCellSelected,
                    day.isToday && !isSelected && styles.weekDayCellToday,
                  ]}
                  onPress={() => setSelectedDateStr(day.jalaliDateStr)}
                >
                  <AppText
                    variant="caption"
                    color={isSelected ? colors.primaryOn : colors.textMuted}
                    align="center"
                  >
                    {day.weekdayLabel.slice(0, 1)}
                  </AppText>
                  <AppText
                    variant="label"
                    color={isSelected ? colors.primaryOn : colors.text}
                    align="center"
                  >
                    {toPersianDigits(day.jalaliDay)}
                  </AppText>
                  {hasMedication ? (
                    <View
                      style={[
                        styles.dotIndicator,
                        isSelected && { backgroundColor: colors.primaryOn },
                      ]}
                    />
                  ) : (
                    <View style={styles.dotPlaceholder} />
                  )}
                </Pressable>
              );
            })}
          </View>

          {/* Selected Date Header */}
          <View style={styles.selectedDateHeader}>
            <AppText variant="title">
              {toPersianDigits(
                (() => {
                  const dayObj = weekDays.find((d) => d.jalaliDateStr === selectedDateStr);
                  if (dayObj) {
                    return `${dayObj.weekdayLabel} ${dayObj.jalaliDay} ${JALALI_MONTH_NAMES[dayObj.jalaliMonth - 1]} ${dayObj.jalaliYear}`;
                  }
                  return selectedDateStr;
                })(),
              )}
            </AppText>
          </View>

          {/* Occurrences List for Selected Day */}
          {setupRequired ? (
            <EmptyState title={t.firstSetupTitle} body={t.firstSetupBody} />
          ) : !selectedDayItems.length ? (
            <EmptyState title={t.empty} body="برنامه دارویی برای این روز ثبت نشده است." />
          ) : (
            selectedDayItems.map(renderProgramCard)
          )}
        </View>
      ) : null}

      {/* TAB 3: CALENDAR */}
      {activeTab === "calendar" ? (
        <View style={styles.tabContent}>
          {/* Month Navigation Controls */}
          <View style={styles.navRow}>
            <Pressable
              style={styles.navButton}
              onPress={() => {
                if (calMonth === 1) {
                  setCalYear((y) => y - 1);
                  setCalMonth(12);
                } else {
                  setCalMonth((m) => m - 1);
                }
              }}
              accessibilityLabel="ماه قبل"
            >
              <AppText variant="label" color={colors.primary}>
                {"‹ ماه قبل"}
              </AppText>
            </Pressable>

            <View style={styles.navCenter}>
              <AppText variant="title" align="center">
                {formatJalaliMonthYear(calYear, calMonth)}
              </AppText>
              {calYear !== todayJalali.year || calMonth !== todayJalali.month ? (
                <Pressable
                  style={styles.todayPill}
                  onPress={() => {
                    setCalYear(todayJalali.year);
                    setCalMonth(todayJalali.month);
                    setSelectedDateStr(todayJalali.formatted);
                  }}
                >
                  <AppText variant="caption" color={colors.primary}>
                    {t.today}
                  </AppText>
                </Pressable>
              ) : null}
            </View>

            <Pressable
              style={styles.navButton}
              onPress={() => {
                if (calMonth === 12) {
                  setCalYear((y) => y + 1);
                  setCalMonth(1);
                } else {
                  setCalMonth((m) => m + 1);
                }
              }}
              accessibilityLabel="ماه بعد"
            >
              <AppText variant="label" color={colors.primary}>
                {"ماه بعد ›"}
              </AppText>
            </Pressable>
          </View>

          {/* Weekday Header Row */}
          <View style={styles.calendarHeaderRow}>
            {JALALI_WEEKDAYS.map((wd) => (
              <View key={wd.code} style={styles.calendarHeaderCell}>
                <AppText variant="caption" color={colors.textMuted} align="center">
                  {wd.label.slice(0, 1)}
                </AppText>
              </View>
            ))}
          </View>

          {/* Month Grid */}
          <View style={styles.calendarGrid}>
            {monthGrid.map((row, rIdx) => (
              <View key={rIdx} style={styles.calendarRow}>
                {row.map((cell) => {
                  const isSelected = selectedDateStr === cell.jalaliDateStr;
                  const hasMedication = Boolean(itemsByDay[cell.jalaliDateStr]?.length);
                  return (
                    <Pressable
                      key={cell.jalaliDateStr}
                      style={[
                        styles.calendarCell,
                        isSelected && styles.calendarCellSelected,
                        cell.isToday && !isSelected && styles.calendarCellToday,
                        !cell.isCurrentMonth && styles.calendarCellDimmed,
                      ]}
                      onPress={() => setSelectedDateStr(cell.jalaliDateStr)}
                    >
                      <AppText
                        variant="label"
                        color={
                          isSelected
                            ? colors.primaryOn
                            : !cell.isCurrentMonth
                              ? colors.textMuted
                              : colors.text
                        }
                        align="center"
                      >
                        {toPersianDigits(cell.dayNumber)}
                      </AppText>
                      {hasMedication ? (
                        <View
                          style={[
                            styles.dotIndicator,
                            isSelected && { backgroundColor: colors.primaryOn },
                          ]}
                        />
                      ) : (
                        <View style={styles.dotPlaceholder} />
                      )}
                    </Pressable>
                  );
                })}
              </View>
            ))}
          </View>

          {/* Selected Date Header */}
          <View style={styles.selectedDateHeader}>
            <AppText variant="title">
              {toPersianDigits(
                (() => {
                  const parsed = parseJalaliStr(selectedDateStr);
                  if (parsed) {
                    const monthName = JALALI_MONTH_NAMES[parsed.month - 1] ?? "";
                    return `${parsed.day} ${monthName} ${parsed.year}`;
                  }
                  return selectedDateStr;
                })(),
              )}
            </AppText>
          </View>

          {/* Occurrences List for Selected Day */}
          {setupRequired ? (
            <EmptyState title={t.firstSetupTitle} body={t.firstSetupBody} />
          ) : !selectedDayItems.length ? (
            <EmptyState title={t.empty} body="برنامه دارویی برای این روز ثبت نشده است." />
          ) : (
            selectedDayItems.map(renderProgramCard)
          )}
        </View>
      ) : null}

      {/* FAB: Add Medication */}
      {can(PERMISSIONS.MANAGE_MEDICATION) && !setupRequired ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t.addMedication}
          onPress={() => router.push("/(app)/program/add?kind=medication")}
          style={styles.fab}
        >
          <Icon name="plus" color={colors.primaryOn} width={14} height={14} />
        </Pressable>
      ) : null}
    </Screen>
  );
}

function parseJalaliStr(str: string): { year: number; month: number; day: number } | null {
  const parts = str.split("/");
  if (parts.length === 3) {
    return { year: Number(parts[0]), month: Number(parts[1]), day: Number(parts[2]) };
  }
  return null;
}

const styles = StyleSheet.create({
  tabs: {
    flexDirection: "row",
    backgroundColor: colors.surfaceSoft,
    borderRadius: radius.sm,
    padding: 4,
    marginBottom: spacing.md,
  },
  tab: { flex: 1, paddingVertical: spacing.sm, borderRadius: 4 },
  tabActive: { backgroundColor: colors.background },
  tabContent: { gap: spacing.sm },
  navRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: spacing.xs,
    marginBottom: spacing.xs,
  },
  navButton: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  navCenter: {
    alignItems: "center",
  },
  todayPill: {
    marginTop: 2,
    paddingHorizontal: 8,
    paddingVertical: 2,
    backgroundColor: colors.surfaceSoft,
    borderRadius: radius.sm,
  },
  weekStrip: {
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: colors.surface,
    padding: spacing.xs,
    borderRadius: radius.md,
    marginBottom: spacing.sm,
  },
  weekDayCell: {
    flex: 1,
    alignItems: "center",
    paddingVertical: spacing.sm,
    borderRadius: radius.sm,
    marginHorizontal: 2,
  },
  weekDayCellSelected: {
    backgroundColor: colors.primary,
  },
  weekDayCellToday: {
    borderWidth: 1,
    borderColor: colors.primary,
  },
  calendarHeaderRow: {
    flexDirection: "row",
    paddingVertical: spacing.xs,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.borderMuted,
  },
  calendarHeaderCell: {
    flex: 1,
    alignItems: "center",
  },
  calendarGrid: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.xs,
    marginBottom: spacing.sm,
  },
  calendarRow: {
    flexDirection: "row",
    marginVertical: 2,
  },
  calendarCell: {
    flex: 1,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.sm,
    marginHorizontal: 2,
  },
  calendarCellSelected: {
    backgroundColor: colors.primary,
  },
  calendarCellToday: {
    borderWidth: 1,
    borderColor: colors.primary,
  },
  calendarCellDimmed: {
    opacity: 0.35,
  },
  dotIndicator: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.primary,
    marginTop: 2,
  },
  dotPlaceholder: {
    width: 4,
    height: 4,
    marginTop: 2,
  },
  selectedDateHeader: {
    marginTop: spacing.xs,
    marginBottom: spacing.xs,
  },
  row: { flexDirection: "row", gap: spacing.md, alignItems: "flex-start" },
  fab: {
    position: "absolute",
    left: spacing.lg,
    bottom: 96,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
});
