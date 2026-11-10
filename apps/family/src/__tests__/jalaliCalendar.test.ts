import {
  formatJalaliDisplay,
  formatJalaliMonthYear,
  getDaysInJalaliMonth,
  getJalaliMonthGrid,
  getJalaliWeekDays,
  getPersianWeekdayIndex,
  gregorianToJalali,
  isJalaliLeapYear,
  jalaliToGregorian,
} from "../services/program/jalali";
import { formatPersianDate } from "../i18n/dates";

describe("Jalali Calendar Algorithms", () => {
  it("converts Gregorian to Jalali accurately", () => {
    // 2026-11-10 is 1405-08-19 (19 Aban 1405)
    const [jy, jm, jd] = gregorianToJalali(2026, 11, 10);
    expect(jy).toBe(1405);
    expect(jm).toBe(8);
    expect(jd).toBe(19);

    // 2025-03-21 is 1404-01-01 (Nowruz 1404)
    const [ny, nm, nd] = gregorianToJalali(2025, 3, 21);
    expect(ny).toBe(1404);
    expect(nm).toBe(1);
    expect(nd).toBe(1);
  });

  it("converts Jalali back to Gregorian correctly", () => {
    const [gy, gm, gd] = jalaliToGregorian(1405, 8, 19);
    expect(gy).toBe(2026);
    expect(gm).toBe(11);
    expect(gd).toBe(10);
  });

  it("correctly identifies Jalali leap years and month lengths", () => {
    // 1403 is a leap year (Esfand has 30 days)
    expect(isJalaliLeapYear(1403)).toBe(true);
    expect(getDaysInJalaliMonth(1403, 12)).toBe(30);

    // 1404 and 1405 are common years (Esfand has 29 days)
    expect(isJalaliLeapYear(1404)).toBe(false);
    expect(getDaysInJalaliMonth(1404, 12)).toBe(29);
    expect(isJalaliLeapYear(1405)).toBe(false);
    expect(getDaysInJalaliMonth(1405, 12)).toBe(29);

    // Months 1-6 have 31 days
    expect(getDaysInJalaliMonth(1405, 1)).toBe(31);
    expect(getDaysInJalaliMonth(1405, 6)).toBe(31);

    // Months 7-11 have 30 days
    expect(getDaysInJalaliMonth(1405, 7)).toBe(30);
    expect(getDaysInJalaliMonth(1405, 8)).toBe(30);
    expect(getDaysInJalaliMonth(1405, 11)).toBe(30);
  });

  it("computes Persian weekday index with Saturday as index 0", () => {
    // 2026-11-07 was Saturday -> index 0 (شنبه)
    const sat = new Date(2026, 10, 7);
    expect(getPersianWeekdayIndex(sat)).toBe(0);

    // 2026-11-08 was Sunday -> index 1 (یکشنبه)
    const sun = new Date(2026, 10, 8);
    expect(getPersianWeekdayIndex(sun)).toBe(1);

    // 2026-11-13 was Friday -> index 6 (جمعه)
    const fri = new Date(2026, 10, 13);
    expect(getPersianWeekdayIndex(fri)).toBe(6);
  });

  it("generates 7 days of the week starting from Saturday", () => {
    const ref = new Date(2026, 10, 10); // Tuesday 2026-11-10
    const week = getJalaliWeekDays(ref, 0);

    expect(week).toHaveLength(7);
    expect(week[0].weekdayCode).toBe("SAT");
    expect(week[0].weekdayLabel).toBe("شنبه");
    expect(week[6].weekdayCode).toBe("FRI");
    expect(week[6].weekdayLabel).toBe("جمعه");
  });

  it("generates a full month calendar grid", () => {
    // Month 8 (Aban) of 1405
    const grid = getJalaliMonthGrid(1405, 8);
    expect(grid.length).toBeGreaterThanOrEqual(4);
    expect(grid.length).toBeLessThanOrEqual(6);

    // Every row must have 7 cells
    for (const row of grid) {
      expect(row).toHaveLength(7);
    }

    // Verify day numbers in the month are present
    const inMonthCells = grid.flat().filter((c) => c.isCurrentMonth);
    expect(inMonthCells).toHaveLength(30);
    expect(inMonthCells[0].dayNumber).toBe(1);
    expect(inMonthCells[29].dayNumber).toBe(30);
  });

  it("formatPersianDate returns pure Jalali date string in Persian digits", () => {
    const d = new Date(2026, 10, 10); // 2026-11-10 -> 19 Aban 1405
    const formatted = formatPersianDate(d);
    expect(formatted).toContain("آبان");
    expect(formatted).toContain("۱۴۰۵");
    expect(formatted).toContain("۱۹");
    // Ensure no Gregorian English months appear
    expect(formatted).not.toContain("November");
    expect(formatted).not.toContain("2026");

    const directDisplay = formatJalaliDisplay(d);
    expect(directDisplay).toBe(formatted);
  });

  it("formatJalaliMonthYear produces expected output", () => {
    const str = formatJalaliMonthYear(1405, 8);
    expect(str).toContain("آبان");
    expect(str).toContain("۱۴۰۵");
  });
});
