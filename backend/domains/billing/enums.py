from django.db import models


class InvoiceStatus(models.TextChoices):
    """Lifecycle states for Invoice.

    DRAFT   — Reserved for future two-phase invoice creation (create draft → finalize).
              No current service produces this status; invoices are created directly as UNPAID.
    UNPAID  — Initial state. Invoice awaiting payment.
    PAID    — Terminal. Settled via settle_invoice(). Immutable after settlement.
    VOID    — Terminal. Cancelled/unpaid invoice via void_invoice().
    REFUNDED — Reserved for future refund flows. No transition function exists yet;
               will require a PAID→REFUNDED service when refund support is added.
    """
    DRAFT = "DRAFT", "Draft"
    UNPAID = "UNPAID", "Unpaid"
    PAID = "PAID", "Paid"
    VOID = "VOID", "Void"
    REFUNDED = "REFUNDED", "Refunded"


class PaymentAttemptStatus(models.TextChoices):
    INITIATED = "INITIATED", "Initiated"
    REDIRECTED = "REDIRECTED", "Redirected"
    SUCCESSFUL = "SUCCESSFUL", "Successful"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class Currency(models.TextChoices):
    TOMAN = "TOMAN", "Toman"
    IRR = "IRR", "Iranian Rial"
    USD = "USD", "US Dollar"


class BillingInterval(models.TextChoices):
    MONTHLY = "MONTHLY", "Monthly"
    ANNUAL = "ANNUAL", "Annual"


class PaymentProviderType(models.TextChoices):
    FAKE = "FAKE", "Fake"
    ZARINPAL = "ZARINPAL", "ZarinPal"
    STRIPE = "STRIPE", "Stripe"
