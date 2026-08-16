import { hasPermission } from "../permissions/codes";

describe("permission guard", () => {
  it("allows only granted permission codes", () => {
    const granted = ["VIEW_ELDER_STATUS", "MANAGE_CONTACTS"] as const;
    expect(hasPermission(granted, "VIEW_ELDER_STATUS")).toBe(true);
    expect(hasPermission(granted, "MANAGE_MEDICATION")).toBe(false);
  });

  it("does not treat role names as access", () => {
    const granted = ["VIEW_ELDER_STATUS"] as const;
    expect(hasPermission(granted, "MANAGE_MEMBERS")).toBe(false);
  });
});
