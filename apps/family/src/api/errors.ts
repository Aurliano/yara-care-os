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

export function mapMessagingError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return t.messagePermissionDenied;
    }
    if (typeof error.body?.detail === "string" && error.body.detail.trim()) {
      return error.body.detail;
    }
  }
  return t.messageSendFailed;
}

export function getAppErrorDisplay(error: unknown): { title: string; body: string } {
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return {
        title: "عدم دسترسی",
        body: "شما مجوز دسترسی به این بخش از پرونده سالمند را ندارید.",
      };
    }
    if (error.status === 404) {
      return {
        title: "یافت نشد",
        body: "اطلاعات مورد نظر در سامانه ثبت نشده یا حذف شده است.",
      };
    }
    if (error.status >= 500) {
      return {
        title: "خطای موقت سرور",
        body: "سامانه برای چند لحظه با اختلال مواجه شده است. لطفاً اندکی بعد دوباره تلاش کنید.",
      };
    }
  }

  const message = error instanceof Error ? error.message.toLowerCase() : "";
  if (message.includes("network") || message.includes("failed to fetch") || message.includes("timeout")) {
    return {
      title: "عدم اتصال به اینترنت",
      body: "ارتباط با سرور برقرار نشد. لطفاً اتصال اینترنت گوشی خود را بررسی فرمایید.",
    };
  }

  return {
    title: t.errorTitle,
    body: t.errorBody,
  };
}
