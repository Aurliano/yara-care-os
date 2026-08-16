import { t } from "../i18n";
import type { ApiErrorBody } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | null;

  constructor(status: number, body: ApiErrorBody | null, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function mapInvitationError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return t.errorBody;
  }
  const detail = (error.body?.detail ?? error.message).toString();
  if (error.status === 404) {
    return t.inviteNotFound;
  }
  if (error.status === 403) {
    return t.accessDenied;
  }
  if (detail.includes("expired")) {
    return t.inviteExpired;
  }
  if (detail.includes("cannot be accepted") || detail.includes("already")) {
    return t.inviteInvalid;
  }
  return t.inviteInvalid;
}

export function mapAccessError(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return t.accessDenied;
  }
  return t.errorBody;
}

export function isPermissionDenied(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403;
}
