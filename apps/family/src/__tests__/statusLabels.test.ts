import { careActivityStatusLabel, completionStateLabel } from "../i18n/labels";

describe("Persian status labels", () => {
  it("does not expose raw care-activity enums", () => {
    expect(careActivityStatusLabel("ACTIVE")).toBe("فعال");
    expect(careActivityStatusLabel("PAUSED")).toBe("متوقف");
  });

  it("does not expose raw completion enums", () => {
    expect(completionStateLabel("MEDICATION_TAKEN")).toBe("دارو مصرف شد");
    expect(completionStateLabel("MEDICATION_MISSED")).toBe("انجام نشد");
  });
});
