import { toLatinDigits } from "../../i18n/numerals";

export const TEHRAN_TIMEZONE = "Asia/Tehran";

function pad2(value: string): string {
  return value.padStart(2, "0");
}

export function todayPartsInTehran(now = new Date()): { date: string; time: string } {
  const date = new Intl.DateTimeFormat("en-CA", {
    timeZone: TEHRAN_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
  const time = new Intl.DateTimeFormat("en-GB", {
    timeZone: TEHRAN_TIMEZONE,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    hourCycle: "h23",
  }).format(now);
  return { date, time };
}

export function combineTehranDateTime(dateYmd: string, timeHm: string): string | null {
  const date = toLatinDigits(dateYmd).trim();
  const time = toLatinDigits(timeHm).trim();
  const dateMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  const timeMatch = /^(\d{1,2}):(\d{2})$/.exec(time);
  if (!dateMatch || !timeMatch) {
    return null;
  }
  const hours = Number(timeMatch[1]);
  const minutes = Number(timeMatch[2]);
  if (hours > 23 || minutes > 59) {
    return null;
  }
  const iso = `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}T${pad2(String(hours))}:${pad2(String(minutes))}:00+03:30`;
  if (Number.isNaN(new Date(iso).getTime())) {
    return null;
  }
  return iso;
}

export function onceRecurrence(): { type: "once" } {
  return { type: "once" };
}
