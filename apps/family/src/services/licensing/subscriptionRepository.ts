import { ApiError } from "../../api/errors";
import type { BillingInterval, License, Plan } from "../../api/types";
import { formatPersianDate, t, toPersianDigits } from "../../i18n";

export type LicenseDisplayStatus =
  | "ACTIVE"
  | "EXPIRED"
  | "SUSPENDED"
  | "REVOKED"
  | "NO_LICENSE";

export type SubscriptionPresentation = {
  license: License | null;
  displayStatus: LicenseDisplayStatus;
  statusLabel: string;
  statusTone: "success" | "warning" | "error" | "neutral";
  validUntilFormatted: string | null;
  planName: string | null;
};

/**
 * Maps the server-authoritative License entity to a caregiver-friendly presentation model.
 * Preserves the backend status semantics and handles expired dates gracefully.
 */
export function mapLicenseToPresentation(
  license: License | null,
  plans: Plan[] = [],
  now: Date = new Date(),
): SubscriptionPresentation {
  if (!license) {
    return {
      license: null,
      displayStatus: "NO_LICENSE",
      statusLabel: t.noActiveSubscription,
      statusTone: "neutral",
      validUntilFormatted: null,
      planName: null,
    };
  }

  const matchedPlan = plans.find((p) => p.code === license.plan_code);
  const planName = matchedPlan ? matchedPlan.name : license.plan_code;

  const validUntilDate = license.valid_until ? new Date(license.valid_until) : null;
  const isPast = validUntilDate ? validUntilDate.getTime() < now.getTime() : false;

  let displayStatus: LicenseDisplayStatus = "NO_LICENSE";
  let statusLabel: string = t.statusActive;
  let statusTone: "success" | "warning" | "error" | "neutral" = "success";

  if (license.status === "ACTIVE") {
    if (isPast) {
      displayStatus = "EXPIRED";
      statusLabel = t.statusExpired;
      statusTone = "warning";
    } else {
      displayStatus = "ACTIVE";
      statusLabel = t.statusActive;
      statusTone = "success";
    }
  } else if (license.status === "EXPIRED") {
    displayStatus = "EXPIRED";
    statusLabel = t.statusExpired;
    statusTone = "warning";
  } else if (license.status === "SUSPENDED") {
    displayStatus = "SUSPENDED";
    statusLabel = t.statusSuspended;
    statusTone = "warning";
  } else if (license.status === "REVOKED") {
    displayStatus = "REVOKED";
    statusLabel = t.statusRevoked;
    statusTone = "error";
  }

  const validUntilFormatted = validUntilDate
    ? formatPersianDate(validUntilDate)
    : null;

  return {
    license,
    displayStatus,
    statusLabel,
    statusTone,
    validUntilFormatted,
    planName,
  };
}

/**
 * Formats a server-provided amount and currency for presentation.
 * Note: Formatting is display-only. The client must never perform business calculation or currency conversion.
 */
export function formatPrice(amount: string | number, currency: string): string {
  const numeric = typeof amount === "number" ? amount : parseInt(amount, 10);
  if (Number.isNaN(numeric)) {
    return `${toPersianDigits(amount)} ${currency}`;
  }
  // Format with thousands separator
  const formattedWithCommas = numeric.toLocaleString("en-US");
  const currencyLabel =
    currency.toUpperCase() === "TOMAN" ? t.toman : currency;
  return `${toPersianDigits(formattedWithCommas)} ${currencyLabel}`;
}

/**
 * Localizes billing interval into Persian display text.
 */
export function intervalLabel(interval: BillingInterval): string {
  switch (interval) {
    case "ANNUAL":
      return t.intervalAnnual;
    case "MONTHLY":
    default:
      return t.intervalMonthly;
  }
}

/**
 * Maps checkout-related errors to calm Persian user messages.
 */
export function mapCheckoutError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return t.permissionDeniedManageSubscription;
    }
    if (error.status === 404) {
      return t.planOrElderNotFound;
    }
    if (typeof error.body?.detail === "string" && error.body.detail.trim()) {
      return error.body.detail;
    }
    return t.checkoutGeneralError;
  }
  return t.checkoutNetworkError;
}
