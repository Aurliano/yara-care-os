const PERSIAN_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"] as const;

export function toPersianDigits(value: string | number): string {
  return String(value).replace(/\d/g, (digit) => PERSIAN_DIGITS[Number(digit)]);
}

export function toLatinDigits(value: string): string {
  return value
    .replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)));
}

export function normalizePhone(value: string): string {
  const latin = toLatinDigits(value).replace(/[\s\-\(\)\.]+/g, "").trim();
  if (latin.startsWith("00989") && latin.length === 14) {
    return `+98${latin.slice(4)}`;
  }
  if (latin.startsWith("09") && latin.length === 11) {
    return `+98${latin.slice(1)}`;
  }
  if (latin.startsWith("9") && latin.length === 10) {
    return `+98${latin}`;
  }
  return latin;
}
