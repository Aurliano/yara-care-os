import { ApiError, mapInvitationError } from "../api/errors";

describe("invitation errors", () => {
  it("maps expired invitation", () => {
    const error = new ApiError(400, { detail: "Invitation has expired." }, "Invitation has expired.");
    expect(mapInvitationError(error)).toContain("منقضی");
  });

  it("maps missing invite code", () => {
    const error = new ApiError(404, { detail: "Not found." }, "Not found.");
    expect(mapInvitationError(error)).toContain("پیدا نشد");
  });

  it("maps forbidden", () => {
    const error = new ApiError(403, { detail: "Forbidden" }, "Forbidden");
    expect(mapInvitationError(error)).toContain("اجازه");
  });
});
