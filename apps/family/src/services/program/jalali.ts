import { toLatinDigits, toPersianDigits } from "../../i18n/numerals";

export const TEHRAN_TIMEZONE = "Asia/Tehran";

export const JALALI_WEEKDAYS = [
  { code: "SAT", label: "شنبه" },
  { code: "SUN", label: "یکشنبه" },
  { code: "MON", label: "دوشنبه" },
  { code: "TUE", label: "سه‌شنبه" },
  { code: "WED", label: "چهارشنبه" },
  { code: "THU", label: "پنجشنبه" },
  { code: "FRI", label: "جمعه" },
] as const;

export const JALALI_MONTH_NAMES = [
  "فروردین",
  "اردیبهشت",
  "خرداد",
  "تیر",
  "مرداد",
  "شهریور",
  "مهر",
  "آبان",
  "آذر",
  "دی",
  "بهمن",
  "اسفند",
] as const;

export function gregorianToJalali(gy: number, gm: number, gd: number): [number, number, number] {
  const g_d_m = [0, 31, ((gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const gy2 = gm > 2 ? gy + 1 : gy;
  let days = 355666 + 365 * gy + (((gy2 + 3) / 4) | 0) - (((gy2 + 99) / 100) | 0) + (((gy2 + 399) / 400) | 0) + gd;
  for (let i = 0; i < gm; ++i) days += g_d_m[i];
  let jy = -1595 + 33 * (((days / 12053) | 0));
  days %= 12053;
  jy += 4 * (((days / 1461) | 0));
  days %= 1461;
  if (days > 365) {
    jy += (((days - 1) / 365) | 0);
    days = (days - 1) % 365;
  }
  const jm = days < 186 ? 1 + (((days / 31) | 0)) : 7 + ((((days - 186) / 30) | 0));
  const jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
  return [jy, jm, jd];
}

export function jalaliToGregorian(jy: number, jm: number, jd: number): [number, number, number] {
  let gy = jy <= 979 ? 621 : 1600;
  jy -= jy <= 979 ? 0 : 979;
  let days =
    365 * jy +
    (((jy / 33) | 0)) * 8 +
    ((((jy % 33) + 3) / 4) | 0) +
    78 +
    jd +
    (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186);
  gy += 400 * (((days / 146097) | 0));
  days %= 146097;
  if (days > 36524) {
    gy += 100 * (((--days / 36524) | 0));
    days %= 36524;
    if (days >= 365) days++;
  }
  gy += 4 * (((days / 1461) | 0));
  days %= 1461;
  if (days > 365) {
    gy += (((days - 1) / 365) | 0);
    days = (days - 1) % 365;
  }
  let gd = days + 1;
  let gm: number;
  const isLeap = (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0;
  const sal_a = [0, 31, isLeap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  for (gm = 1; gm <= 12; gm++) {
    if (gd <= sal_a[gm]) break;
    gd -= sal_a[gm];
  }
  return [gy, gm, gd];
}

function pad2(num: number): string {
  return String(num).padStart(2, "0");
}

export function isJalaliLeapYear(jy: number): boolean {
  const [gy, gm, gd] = jalaliToGregorian(jy, 12, 30);
  const [checkJy, checkJm, checkJd] = gregorianToJalali(gy, gm, gd);
  return checkJy === jy && checkJm === 12 && checkJd === 30;
}

export function getDaysInJalaliMonth(jy: number, jm: number): number {
  if (jm < 1 || jm > 12) return 0;
  if (jm <= 6) return 31;
  if (jm <= 11) return 30;
  return isJalaliLeapYear(jy) ? 30 : 29;
}

export function getPersianWeekdayIndex(date: Date): number {
  const gDay = date.getDay(); // 0 = Sun, 1 = Mon, ..., 6 = Sat
  return (gDay + 1) % 7; // 0 = Sat (شنبه), 1 = Sun, ..., 6 = Fri (جمعه)
}

export function isSameDay(d1: Date, d2: Date): boolean {
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

export function getTodayJalali(date = new Date()): { year: number; month: number; day: number; formatted: string } {
  const [jy, jm, jd] = gregorianToJalali(date.getFullYear(), date.getMonth() + 1, date.getDate());
  return {
    year: jy,
    month: jm,
    day: jd,
    formatted: `${jy}/${pad2(jm)}/${pad2(jd)}`,
  };
}

export function parseJalaliDateString(input: string): { year: number; month: number; day: number } | null {
  const latin = toLatinDigits(input).trim().replace(/-/g, "/");
  const match = /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec(latin);
  if (!match) {
    return null;
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);

  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return null;
  }
  if (month > 6 && day > 30) {
    return null;
  }
  return { year, month, day };
}

export function jalaliToTehranIso(
  jalaliStr: string,
  timeHm = "00:00",
): string | null {
  const parsedDate = parseJalaliDateString(jalaliStr);
  if (!parsedDate) {
    return null;
  }
  const latinTime = toLatinDigits(timeHm).trim();
  const timeMatch = /^(\d{1,2}):(\d{2})$/.exec(latinTime);
  if (!timeMatch) {
    return null;
  }
  const hours = Number(timeMatch[1]);
  const minutes = Number(timeMatch[2]);
  if (hours > 23 || minutes > 59) {
    return null;
  }

  const [gy, gm, gd] = jalaliToGregorian(parsedDate.year, parsedDate.month, parsedDate.day);
  const iso = `${gy}-${pad2(gm)}-${pad2(gd)}T${pad2(hours)}:${pad2(minutes)}:00+03:30`;
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return iso;
}

export function formatJalaliDisplay(isoOrDate: string | Date): string {
  const d = typeof isoOrDate === "string" ? new Date(isoOrDate) : isoOrDate;
  if (Number.isNaN(d.getTime())) {
    return "—";
  }
  const [jy, jm, jd] = gregorianToJalali(d.getFullYear(), d.getMonth() + 1, d.getDate());
  const monthName = JALALI_MONTH_NAMES[jm - 1] ?? "";
  return toPersianDigits(`${jd} ${monthName} ${jy}`);
}

export function formatJalaliMonthYear(jy: number, jm: number): string {
  const monthName = JALALI_MONTH_NAMES[jm - 1] ?? "";
  return toPersianDigits(`${monthName} ${jy}`);
}

export function formatJalaliDayMonth(isoOrDate: string | Date): string {
  const d = typeof isoOrDate === "string" ? new Date(isoOrDate) : isoOrDate;
  if (Number.isNaN(d.getTime())) {
    return "—";
  }
  const [, jm, jd] = gregorianToJalali(d.getFullYear(), d.getMonth() + 1, d.getDate());
  const monthName = JALALI_MONTH_NAMES[jm - 1] ?? "";
  return toPersianDigits(`${jd} ${monthName}`);
}

export function addDaysToJalali(jalaliStr: string, daysToAdd: number): string | null {
  const parsed = parseJalaliDateString(jalaliStr);
  if (!parsed) return null;
  const [gy, gm, gd] = jalaliToGregorian(parsed.year, parsed.month, parsed.day);
  const d = new Date(gy, gm - 1, gd);
  d.setDate(d.getDate() + daysToAdd);
  const [jy, jm, jd] = gregorianToJalali(d.getFullYear(), d.getMonth() + 1, d.getDate());
  return `${jy}/${pad2(jm)}/${pad2(jd)}`;
}

export interface JalaliDayItem {
  date: Date;
  jalaliYear: number;
  jalaliMonth: number;
  jalaliDay: number;
  jalaliDateStr: string;
  weekdayCode: (typeof JALALI_WEEKDAYS)[number]["code"];
  weekdayLabel: string;
  isToday: boolean;
}

export function getJalaliWeekDays(refDate = new Date(), weekOffset = 0): JalaliDayItem[] {
  const base = new Date(refDate.getFullYear(), refDate.getMonth(), refDate.getDate());
  const weekdayIndex = getPersianWeekdayIndex(base);
  const sat = new Date(base);
  sat.setDate(base.getDate() - weekdayIndex + weekOffset * 7);

  const today = new Date();
  const days: JalaliDayItem[] = [];
  for (let i = 0; i < 7; i++) {
    const cur = new Date(sat);
    cur.setDate(sat.getDate() + i);
    const [jy, jm, jd] = gregorianToJalali(cur.getFullYear(), cur.getMonth() + 1, cur.getDate());
    days.push({
      date: cur,
      jalaliYear: jy,
      jalaliMonth: jm,
      jalaliDay: jd,
      jalaliDateStr: `${jy}/${pad2(jm)}/${pad2(jd)}`,
      weekdayCode: JALALI_WEEKDAYS[i].code,
      weekdayLabel: JALALI_WEEKDAYS[i].label,
      isToday: isSameDay(cur, today),
    });
  }
  return days;
}

export interface JalaliCalendarCell {
  dayNumber: number;
  jalaliDateStr: string;
  date: Date;
  isCurrentMonth: boolean;
  isToday: boolean;
  weekdayIndex: number;
}

export function getJalaliMonthGrid(jy: number, jm: number): JalaliCalendarCell[][] {
  const totalDays = getDaysInJalaliMonth(jy, jm);
  const [firstGy, firstGm, firstGd] = jalaliToGregorian(jy, jm, 1);
  const firstDate = new Date(firstGy, firstGm - 1, firstGd);
  const startWeekday = getPersianWeekdayIndex(firstDate);

  const today = new Date();
  const cells: JalaliCalendarCell[] = [];

  const prevJm = jm === 1 ? 12 : jm - 1;
  const prevJy = jm === 1 ? jy - 1 : jy;
  const prevTotalDays = getDaysInJalaliMonth(prevJy, prevJm);

  for (let i = startWeekday - 1; i >= 0; i--) {
    const dayNum = prevTotalDays - i;
    const [gy, gm, gd] = jalaliToGregorian(prevJy, prevJm, dayNum);
    const d = new Date(gy, gm - 1, gd);
    cells.push({
      dayNumber: dayNum,
      jalaliDateStr: `${prevJy}/${pad2(prevJm)}/${pad2(dayNum)}`,
      date: d,
      isCurrentMonth: false,
      isToday: isSameDay(d, today),
      weekdayIndex: getPersianWeekdayIndex(d),
    });
  }

  for (let d = 1; d <= totalDays; d++) {
    const [gy, gm, gd] = jalaliToGregorian(jy, jm, d);
    const date = new Date(gy, gm - 1, gd);
    cells.push({
      dayNumber: d,
      jalaliDateStr: `${jy}/${pad2(jm)}/${pad2(d)}`,
      date,
      isCurrentMonth: true,
      isToday: isSameDay(date, today),
      weekdayIndex: getPersianWeekdayIndex(date),
    });
  }

  const remaining = (7 - (cells.length % 7)) % 7;
  const nextJm = jm === 12 ? 1 : jm + 1;
  const nextJy = jm === 12 ? jy + 1 : jy;

  for (let d = 1; d <= remaining; d++) {
    const [gy, gm, gd] = jalaliToGregorian(nextJy, nextJm, d);
    const date = new Date(gy, gm - 1, gd);
    cells.push({
      dayNumber: d,
      jalaliDateStr: `${nextJy}/${pad2(nextJm)}/${pad2(d)}`,
      date,
      isCurrentMonth: false,
      isToday: isSameDay(date, today),
      weekdayIndex: getPersianWeekdayIndex(date),
    });
  }

  const rows: JalaliCalendarCell[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    rows.push(cells.slice(i, i + 7));
  }
  return rows;
}

export function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
