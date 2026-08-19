import type { CallSession } from "./model";
import { t } from "../i18n";
import { ApiError } from "../api/errors";
import type { ApiErrorBody } from "../api/types";
import { ActiveCallExistsError } from "./result";
import type { AppResult } from "./result";

export interface CommunicationGateway {
  startCall(
    elderId: string,
    channel: string,
    recipientContactId: string,
  ): Promise<AppResult<CallSession>>;
  endCall(sessionId: string): Promise<AppResult<void>>;
  refreshJoinToken(elderId: string): Promise<AppResult<CallSession>>;
}

export type JoinCredentials = {
  sessionId?: string;
  joinToken: string;
  expiresAt: string;
};

export interface FamilyHttpClient {
  postJson(path: string, body: unknown): Promise<{ status: number; body: unknown }>;
}

export class HttpCommunicationGateway implements CommunicationGateway {
  constructor(
    private readonly http: FamilyHttpClient,
    private readonly nowMillis: () => number = () => Date.now(),
  ) {}

  async startCall(
    elderId: string,
    channel: string,
    recipientContactId: string,
  ): Promise<AppResult<CallSession>> {
    return this.requestSession(
      "communication/call/start/",
      {
        elder_id: elderId,
        channel,
        recipient_contact_id: recipientContactId,
      },
      { elderId, channel, recipientContactId },
    );
  }

  async endCall(sessionId: string): Promise<AppResult<void>> {
    const response = await this.http.postJson("communication/call/end/", {
      session_id: sessionId,
    });
    if (response.status >= 200 && response.status < 300) {
      return { ok: true, data: undefined };
    }
    const error = mapHttpError(response.status, response.body);
    return { ok: false, error, message: error.message };
  }

  async refreshJoinToken(elderId: string): Promise<AppResult<CallSession>> {
    return this.requestSession(
      "communication/login-url/",
      { elder_id: elderId },
      { elderId, channel: "", recipientContactId: "" },
    );
  }

  private async requestSession(
    path: string,
    body: unknown,
    context: { elderId: string; channel: string; recipientContactId: string },
  ): Promise<AppResult<CallSession>> {
    const response = await this.http.postJson(path, body);
    if (response.status === 409) {
      const error = new ActiveCallExistsError();
      return { ok: false, error, message: error.message };
    }
    if (response.status < 200 || response.status >= 300) {
      const error = mapHttpError(response.status, response.body);
      return { ok: false, error, message: error.message };
    }
    try {
      return {
        ok: true,
        data: credentialsToSession(response.body, context, this.nowMillis()),
      };
    } catch (caught) {
      const error = caught instanceof Error ? caught : new Error(String(caught));
      return { ok: false, error, message: error.message };
    }
  }
}

function mapHttpError(status: number, body: unknown): Error {
  if (status === 409) {
    return new ActiveCallExistsError();
  }
  const apiBody = typeof body === "object" && body !== null ? (body as ApiErrorBody) : null;
  const detail =
    apiBody && "detail" in apiBody && apiBody.detail != null
      ? String(apiBody.detail)
      : `HTTP ${status}`;
  if (status === 403 || status === 502) {
    return new ApiError(status, apiBody, detail);
  }
  return new Error(detail);
}

export function mapCallFailureMessage(error: unknown): string {
  if (error instanceof ActiveCallExistsError) {
    return t.callBusy;
  }
  const detail =
    error instanceof ApiError
      ? String(error.body?.detail ?? error.message)
      : error instanceof Error
        ? error.message
        : "";
  if (error instanceof ApiError && error.status === 403) {
    return t.callPermissionBody;
  }
  if (detail.includes("not configured")) {
    return t.callProviderNotConfigured;
  }
  if (detail.includes("unreachable")) {
    return t.callProviderUnreachable;
  }
  return t.callFailed;
}

function credentialsToSession(
  body: unknown,
  context: { elderId: string; channel: string; recipientContactId: string },
  nowMillis: number,
): CallSession {
  if (typeof body !== "object" || body === null) {
    throw new Error("Backend join response was empty.");
  }
  const payload = body as Partial<JoinCredentials>;
  if (!payload.joinToken || !payload.expiresAt) {
    throw new Error("Backend join response is missing joinToken or expiresAt.");
  }
  return {
    sessionId: payload.sessionId ?? "",
    elderId: context.elderId,
    channel: context.channel,
    recipientContactId: context.recipientContactId,
    runtimeState: "Connecting",
    joinToken: payload.joinToken,
    expiresAtEpochMillis: parseExpiresAt(payload.expiresAt, nowMillis),
    updatedAtEpochMillis: nowMillis,
    direction: "Outgoing",
  };
}

export function parseExpiresAt(value: string, fallbackNow: number): number {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return fallbackNow + 3_600_000;
  }
  return parsed;
}
