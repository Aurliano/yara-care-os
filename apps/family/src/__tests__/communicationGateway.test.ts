import {
  HttpCommunicationGateway,
  parseExpiresAt,
} from "../communication/CommunicationGateway";
import { ActiveCallExistsError } from "../communication/result";
import type { FamilyHttpClient } from "../communication/CommunicationGateway";

class FakeHttp implements FamilyHttpClient {
  calls: { path: string; body: unknown }[] = [];
  next: { status: number; body: unknown } = { status: 500, body: {} };

  async postJson(path: string, body: unknown): Promise<{ status: number; body: unknown }> {
    this.calls.push({ path, body });
    return this.next;
  }
}

const JOIN_BODY = {
  sessionId: "session-1",
  joinToken: "opaque-join-token",
  expiresAt: "2026-08-16T08:00:00Z",
};

describe("HttpCommunicationGateway", () => {
  it("maps startCall to Backend join credentials", async () => {
    const http = new FakeHttp();
    http.next = { status: 200, body: JOIN_BODY };
    const gateway = new HttpCommunicationGateway(http, () => 0);

    const result = await gateway.startCall("elder-1", "VOICE", "contact-1");

    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    expect(result.data.sessionId).toBe("session-1");
    expect(result.data.joinToken).toBe("opaque-join-token");
    expect(result.data.expiresAtEpochMillis).toBe(Date.parse("2026-08-16T08:00:00Z"));
    expect(http.calls).toEqual([
      {
        path: "communication/call/start/",
        body: {
          elder_id: "elder-1",
          channel: "VOICE",
          recipient_contact_id: "contact-1",
        },
      },
    ]);
  });

  it("maps HTTP 409 to ActiveCallExistsError", async () => {
    const http = new FakeHttp();
    http.next = { status: 409, body: { detail: "active session" } };
    const gateway = new HttpCommunicationGateway(http);

    const result = await gateway.startCall("elder-1", "VOICE", "contact-1");

    expect(result.ok).toBe(false);
    if (result.ok) {
      return;
    }
    expect(result.error).toBeInstanceOf(ActiveCallExistsError);
  });

  it("posts endCall with session_id", async () => {
    const http = new FakeHttp();
    http.next = { status: 200, body: { status: "ended" } };
    const gateway = new HttpCommunicationGateway(http);

    const result = await gateway.endCall("session-1");

    expect(result.ok).toBe(true);
    expect(http.calls[0]).toEqual({
      path: "communication/call/end/",
      body: { session_id: "session-1" },
    });
  });

  it("refreshes joinToken via login-url", async () => {
    const http = new FakeHttp();
    http.next = {
      status: 200,
      body: {
        sessionId: "existing-session",
        joinToken: "refreshed-token",
        expiresAt: "2026-08-16T09:00:00Z",
      },
    };
    const gateway = new HttpCommunicationGateway(http, () => 0);

    const result = await gateway.refreshJoinToken("elder-1");

    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    expect(result.data.sessionId).toBe("existing-session");
    expect(result.data.joinToken).toBe("refreshed-token");
    expect(http.calls[0]).toEqual({
      path: "communication/login-url/",
      body: { elder_id: "elder-1" },
    });
  });

  it("never posts to a Skyroom REST path", async () => {
    const http = new FakeHttp();
    http.next = { status: 200, body: JOIN_BODY };
    const gateway = new HttpCommunicationGateway(http);
    await gateway.startCall("elder-1", "VOICE", "contact-1");
    await gateway.refreshJoinToken("elder-1");
    await gateway.endCall("session-1");

    for (const call of http.calls) {
      expect(call.path).not.toMatch(/skyroom/i);
      expect(call.path).toMatch(/^communication\//);
    }
  });

  it("parseExpiresAt reads ISO-8601", () => {
    expect(parseExpiresAt("2026-08-16T08:00:00Z", 0)).toBe(
      Date.parse("2026-08-16T08:00:00Z"),
    );
  });

  it("parseExpiresAt falls back when the value is invalid", () => {
    expect(parseExpiresAt("not-a-date", 1_000)).toBe(1_000 + 3_600_000);
  });
});
