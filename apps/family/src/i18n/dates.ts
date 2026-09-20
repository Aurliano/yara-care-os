import { toPersianDigits } from "./numerals";

const WEEKDAYS = ["یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"];

export function formatClock(iso: string | Date): string {
  const date = typeof iso === "string" ? new Date(iso) : iso;
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return toPersianDigits(`${hours}:${minutes}`);
}

export function formatRelative(iso: string, now = new Date()): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "زمان نامشخص";
  }
  const diffMs = now.getTime() - date.getTime();
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) {
    return "همین حالا";
  }
  if (minutes < 60) {
    return `${toPersianDigits(minutes)} دقیقه پیش`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 24) {
    return `${toPersianDigits(hours)} ساعت پیش`;
  }
  const days = Math.round(hours / 24);
  return `${toPersianDigits(days)} روز پیش`;
}

export function formatPersianDate(iso: string | Date): string {
  const date = typeof iso === "string" ? new Date(iso) : iso;
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  const formatted = new Intl.DateTimeFormat("fa-IR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
  return toPersianDigits(formatted);
}

export function weekdayName(iso: string | Date): string {
  const date = typeof iso === "string" ? new Date(iso) : iso;
  return WEEKDAYS[date.getDay()] ?? "";
}

export function startOfLocalDay(date = new Date()): Date {
  const ymd = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tehran",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
  return new Date(`${ymd}T00:00:00.000+03:30`);
}

export function endOfLocalDay(date = new Date()): Date {
  const ymd = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tehran",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
  return new Date(`${ymd}T23:59:59.999+03:30`);
}
