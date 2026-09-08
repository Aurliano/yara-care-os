# ADR-016 — Subscription Aggregate, Billing Domain Boundary, and Payment Provider Abstraction

Status: Accepted
Scope: Backend Licensing, Billing Domain, and Payment Infrastructure Architecture
Supersedes: (none)
Related: ADR-010 (Boundaries), ADR-012 (Hub Reminder MVP), ADR-013 (Provider Abstraction Pattern), ADR-015 (Alerts)

---

## Context

Phase 1 (Two-Way Messaging & Communication Engine) has been completed and verified on real hardware. Yara Care OS is now entering Phase 2: Commercialization, Licensing, Billing, and Payments.

In the current codebase:
1. `backend/domains/licensing` contains `Plan`, `Entitlement`, `PlanEntitlement`, `License`, and `LicensePlanHistory`.
2. `Subscription` is documented in `docs/erd-v2.1.md` and `docs/domains/licensing.md`, but has no Django model representation.
3. No billing, invoice, transaction, or financial accounting domain exists.
4. No payment gateway integration or provider abstraction exists.
5. The Android Hub appliance is completely offline-first and must never be constrained by cloud paywalls or network outages.

Before implementing any models or services, the architectural boundaries between commercial subscription periods, functional license entitlements, financial ledger accounting, and external payment transports must be formally established.

---

## Decision

### 1. Subscription Belongs to the Licensing Domain (`domains.licensing`)
- `Subscription` is modeled as an aggregate within `domains.licensing`.
- It represents the **temporal commercial commitment** supporting a `License`.
- **Core Distinction:**
  - `License` answers: *"What capabilities and limits is this Elder permitted to use right now?"* (Functional authorization container).
  - `Subscription` answers: *"For what active time window is this commercial access valid, and how does it renew?"* (Temporal commitment).
  - `Billing` answers: *"What financial charges were issued, and was money received?"* (Financial accounting).
- **Arbitrary Duration Support (Rental & Seasonal Compatibility):**
  `Subscription` uses explicit datetime boundaries (`started_at: datetime`, `expires_at: datetime`). It is intentionally not constrained to fixed 30-day or 365-day enums. This directly supports:
  - 14-day free trials.
  - Standard monthly (30-day) and annual (365-day) recurring terms.
  - Short-term and flexible rental periods (e.g. 7-day or 60-day convalescent Hub leases), matching `DeviceAssignment.assignment_type = RENTED` per `docs/domains/licensing.md` Section 9.

### 2. License Cardinality & Terminal State Handling (`ELDER 1..N LICENSE`)
- The relational schema conforms to ERD V2.1: `ELDER ||--o{ LICENSE : owns` (1-to-many).
- **Runtime Invariant:** An Elder has **at most one ACTIVE License at any given time** (`status = ACTIVE`), enforced via database constraints / partial unique indexing.
- **Normal Plan Transitions:** Standard lifecycle events (Trial completion -> Basic downgrade, Plus -> Premium upgrade, renewals) do NOT issue new License entities. They execute `change_license_plan` on the existing License and record the transition in `LicensePlanHistory`.
- **Terminal State (`REVOKED`):** If a License is terminated due to fraud or administrative action (`status = REVOKED`), it enters an immutable terminal state and cannot be reactivated or expired. In the rare scenario where an Elder's service is legitimately restored after administrative review, a **new License instance** is provisioned for that Elder. This preserves the historical audit trail of the revoked license while respecting the 1-to-many schema.

### 3. Billing is Established as an Independent Supporting Domain (`domains.billing`)
- A new supporting domain `domains.billing` is created to isolate all financial facts.
- **Billing owns:**
  - `Invoice`: Financial obligation, currency, amount, tax, issue date, due date, status (`DRAFT`, `UNPAID`, `PAID`, `VOID`, `REFUNDED`).
  - `InvoiceLineItem`: Itemized breakdown (subscription term, hardware leasing/deposit, discounts).
  - `PaymentAttempt`: Transaction log capturing checkout attempts, gateway authorities, timestamps, and outcomes.
  - `PlanPrice`: Commercial catalog defining currency, billing interval, and pricing tiers separate from functional `Plan` definitions.
- **Billing does NOT own:**
  - Feature entitlements, limits, or user permissions.
  - Direct communication with payment vendor SDKs.
- Cross-domain linkage between Billing and Licensing/Identity uses unconstrained identifier references (`elder_id`, `payer_user_id`, `subscription_id`), preserving loose coupling and preventing cascading locks.

### 4. Payment Gateways Follow the ADR-013 Provider Abstraction Pattern (`backend/infrastructure/payment/`)
- Payment gateways (e.g. ZarinPal, Shaparak IPG, Stripe, BazaarPay) are **Infrastructure Providers**, not domain concepts.
- Neither `Licensing` nor `Billing` contains gateway vendor SDKs, vendor endpoints, or vendor credentials.
- Infrastructure exposes an abstract protocol (`PaymentProvider` port):
  - `request_payment(invoice_id, amount, currency, callback_url, metadata) -> PaymentRequestResult`
  - `verify_payment(provider_reference, payload) -> PaymentVerificationResult`
- A `FakePaymentProvider` is provided for local development, CI/CD, and offline test execution.
- Production credentials (`PAYMENT_GATEWAY_KEY`, `MERCHANT_ID`) reside exclusively in backend environment settings and are never exposed to client applications.

### 5. Hub Offline Immunity Invariant
- The Android Hub is a calm, offline companion appliance dedicated to elder health and medication safety.
- **Invariant:** Under NO circumstances does the Android Hub store, replicate, or evaluate `License`, `Subscription`, or `Billing` state.
- Hub medication alarms, pillbox confirmation, and local sensor evaluations function 100% offline regardless of cloud subscription expiration, unpaid invoices, or internet connectivity outages.
- Entitlement checks are enforced strictly at the cloud backend ingest boundary and the Caregiver (Family) App presentation layer.

### 6. Architectural Exception: Synchronous Payment Settlement & Domain Event Duality
- **The Golden Rule:** In Yara, domains do not directly invoke other domain services; cross-domain coordination is decoupled via Domain Events published to the `event` domain.
- **The Conscious Exception:** Bank gateway return redirects and payment verification webhooks require immediate, sub-second response times to prevent caregiver anxiety and maintain UX confidence upon return from the bank. Introducing an asynchronous message broker / polling queue between payment verification and entitlement activation would degrade mobile checkout UX.
- **Decision:**
  1. An application-level coordinator is granted an **explicit architectural exception** (analogous to the LiveKit session control exception in PROJECT_CONTEXT and ADR-013) to synchronously invoke Licensing (`activate_subscription` / `extend_license`) immediately upon verified invoice settlement in Billing.
  2. **Event Duality:** Concurrently with the synchronous activation, Billing publishes a formal domain event `PaymentSucceeded` to the `event` domain. This event is consumed asynchronously by decoupled subscribers:
     - Audit logging.
     - Caregiver In-App Alert creation (ADR-015).
     - Future push notification and SMS receipt delivery.
     - Outbox reconciliation workers.
  3. Payment verification operations must be strictly idempotent using unique transaction tokens (`idempotency_key` / gateway `authority`). Replaying callbacks must never double-credit a subscription term.

---

## Relational & Identity Binding Rules

1. **Elder Anchoring:**
   `License` is anchored to `identity_access.Elder` (schema: 1..N historical, runtime invariant: at most 1 active). Entitlements belong to the care context of that Elder.
2. **Caregiver Purchase Authority:**
   Only a `User` holding an active `Membership` with `Role: PRIMARY_CAREGIVER` (which grants `PermissionCode.MANAGE_SUBSCRIPTION`) is authorized to initiate checkouts, change plans, or cancel subscriptions for that Elder.
3. **Multi-Caregiver Benefit:**
   All caregivers linked to an Elder share the benefits of the Elder's active license (up to `MAX_CAREGIVERS`). Secondary caregivers do not need separate subscriptions.
4. **Multi-Elder Isolation:**
   Each Elder has an independent `License` and independent `Subscription`. A caregiver caring for multiple elders pays separate subscriptions per Elder.

---

## Consequences

### Positive
- Strict separation between legal access (`License`), temporal term (`Subscription`), and money (`Billing`).
- Instantaneous mobile UX for caregivers upon returning from payment gateways, without losing event-driven audit and notification decoupling.
- Vendor independence: switching payment gateways (e.g. from ZarinPal to Stripe or BazaarPay) requires zero changes to domain models or client contracts.
- High system testability via `FakePaymentProvider` without mocking network calls.
- Total preservation of Hub offline reliability and patient safety.

### Negative / Trade-offs
- Two-step state transition during checkout (`Invoice` settlement -> `Subscription` activation).
- Requires reconciliation handling (outbox / retry) to handle edge-case network splits between payment settlement and license provisioning.

---

## Verification & Compliance

1. Architecture tests in `tests/architecture/test_billing.py` and `test_licensing.py` must enforce:
   - No direct foreign keys between `Billing` and `Licensing`.
   - No imports of payment vendor SDKs within `domains/`.
   - The synchronous billing-to-licensing coordinator is isolated in an approved application orchestration service.
2. Domain unit tests must prove that expired or missing licenses on the cloud never block Android Hub synchronization or alarm execution.
3. API tests must verify that `CanManageSubscription` strictly blocks non-primary caregivers from initiating payments or modifying plans.
