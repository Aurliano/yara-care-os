import { toLatinDigits, toPersianDigits } from "../i18n/numerals";

describe("Persian numerals", () => {
  it("converts latin digits to persian", () => {
    expect(toPersianDigits("20:00")).toBe("۲۰:۰۰");
    expect(toPersianDigits(85)).toBe("۸۵");
  });

  it("converts persian digits back to latin", () => {
    expect(toLatinDigits("۰۹۱۲")).toBe("0912");
  });
});
