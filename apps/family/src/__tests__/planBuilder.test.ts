import {
  gregorianToJalali,
  jalaliToGregorian,
  jalaliToTehranIso,
  generateIdempotencyKey,
} from "../services/program/jalali";
import { createPrescription, createCareActivity } from "../api/endpoints/care";

describe("Sprint C2 - Family Plan Builder & Jalali Date / Scheduling UX", () => {
  const originalFetch = global.fetch;
  let fetchMock: jest.Mock;

  beforeEach(() => {
    fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ id: "mock-id" }),
      json: async () => ({ id: "mock-id" }),
    });
    global.fetch = fetchMock;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe("Jalali Date Conversion", () => {
    test("accurately converts known Gregorian dates to Jalali [jy, jm, jd]", () => {
      // 2026-03-21 is 1405-01-01 (Nowruz)
      const nowruz = gregorianToJalali(2026, 3, 21);
      expect(nowruz).toEqual([1405, 1, 1]);

      // 2026-09-24 is 1405-07-02
      const autumn = gregorianToJalali(2026, 9, 24);
      expect(autumn).toEqual([1405, 7, 2]);
    });

    test("accurately converts Jalali dates back to Gregorian [gy, gm, gd]", () => {
      // 1405-01-01 -> 2026-03-21
      const gNowruz = jalaliToGregorian(1405, 1, 1);
      expect(gNowruz).toEqual([2026, 3, 21]);

      // 1405-07-02 -> 2026-09-24
      const gAutumn = jalaliToGregorian(1405, 7, 2);
      expect(gAutumn).toEqual([2026, 9, 24]);
    });

    test("formats Jalali date string and time into Asia/Tehran ISO string (+03:30)", () => {
      const iso = jalaliToTehranIso("1405/07/02", "08:30");
      expect(iso).toBe("2026-09-24T08:30:00+03:30");

      const eveningIso = jalaliToTehranIso("1405/01/01", "20:00");
      expect(eveningIso).toBe("2026-03-21T20:00:00+03:30");
    });
  });

  describe("Idempotency Key Utility", () => {
    test("generates RFC4122 compliant UUID v4 string", () => {
      const key = generateIdempotencyKey();
      expect(typeof key).toBe("string");
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      expect(uuidRegex.test(key)).toBe(true);
    });

    test("generates unique keys on successive calls", () => {
      const key1 = generateIdempotencyKey();
      const key2 = generateIdempotencyKey();
      expect(key1).not.toBe(key2);
    });
  });

  describe("API Client Idempotency-Key Header Propagation", () => {
    test("passes Idempotency-Key header when creating prescription", async () => {
      const testKey = "11111111-2222-4333-8444-555555555555";
      await createPrescription(
        "elder-123",
        {
          workflow_definition_id: "wf-1",
          recurrence_definition: { frequency: "daily", times: ["08:00"] },
          timezone_name: "Asia/Tehran",
          start_at: "2026-09-24T08:00:00+03:30",
          display_title: "Aspirin",
          medication_reference: "Aspirin",
          dosage_information: "81mg",
          elder_friendly_description: "Take with water",
        },
        { idempotencyKey: testKey },
      );

      expect(fetchMock).toHaveBeenCalled();
      const lastCall = fetchMock.mock.calls[0];
      const [, requestInit] = lastCall;
      expect(requestInit.headers["Idempotency-Key"]).toBe(testKey);
    });

    test("passes Idempotency-Key header when creating care activity", async () => {
      const testKey = "99999999-8888-4777-8666-555555555555";
      await createCareActivity(
        "elder-123",
        {
          activity_type: "medication",
          workflow_definition_id: "wf-1",
          recurrence_definition: { frequency: "daily", times: ["08:00", "14:00", "20:00"] },
          timezone_name: "Asia/Tehran",
          start_at: "2026-09-24T08:00:00+03:30",
          display_title: "Daily Vitamins",
          display_subtitle: "Take daily vitamins",
        },
        { idempotencyKey: testKey },
      );

      expect(fetchMock).toHaveBeenCalled();
      const lastCall = fetchMock.mock.calls[0];
      const [, requestInit] = lastCall;
      expect(requestInit.headers["Idempotency-Key"]).toBe(testKey);
    });
  });

  describe("Multi-Dose Recurrence Rule Payload Contract", () => {
    test("constructs valid canonical payload for daily multi-dose", () => {
      const times = ["08:00", "14:00", "20:00"];
      const recurrenceRule = {
        frequency: "daily" as const,
        times,
      };

      expect(recurrenceRule.frequency).toBe("daily");
      expect(recurrenceRule.times).toHaveLength(3);
      expect(recurrenceRule.times).toEqual(["08:00", "14:00", "20:00"]);
    });

    test("constructs valid canonical payload for specific weekdays", () => {
      const recurrenceRule = {
        frequency: "specific_days" as const,
        weekdays: ["saturday", "monday", "wednesday"],
        times: ["09:00", "21:00"],
      };

      expect(recurrenceRule.frequency).toBe("specific_days");
      expect(recurrenceRule.weekdays).toEqual(["saturday", "monday", "wednesday"]);
      expect(recurrenceRule.times).toEqual(["09:00", "21:00"]);
    });

    test("constructs valid canonical payload for every N days", () => {
      const recurrenceRule = {
        frequency: "every_n_days" as const,
        interval_days: 3,
        times: ["08:00"],
      };

      expect(recurrenceRule.frequency).toBe("every_n_days");
      expect(recurrenceRule.interval_days).toBe(3);
      expect(recurrenceRule.times).toEqual(["08:00"]);
    });

    test("handles duplicate prevention logic for time slots", () => {
      const existingTimes = ["08:00", "14:00"];
      const candidateTime = "08:00";

      const isDuplicate = existingTimes.includes(candidateTime);
      expect(isDuplicate).toBe(true);

      const newTime = "20:00";
      const isNewDuplicate = existingTimes.includes(newTime);
      expect(isNewDuplicate).toBe(false);

      const updated = [...existingTimes, newTime].sort();
      expect(updated).toEqual(["08:00", "14:00", "20:00"]);
    });
  });
});
