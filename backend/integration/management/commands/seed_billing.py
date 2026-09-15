"""Seed MVP billing plans and prices."""

from decimal import Decimal
from django.core.management.base import BaseCommand
from domains.billing.enums import BillingInterval, Currency
from domains.billing.models import PlanPrice


PLAN_PRICES = {
    "BASIC": {
        "interval": BillingInterval.MONTHLY,
        "amount": Decimal("0"),
        "currency": Currency.TOMAN,
    },
    "PLUS": {
        "interval": BillingInterval.MONTHLY,
        "amount": Decimal("100000"),
        "currency": Currency.TOMAN,
    },
    "PREMIUM": {
        "interval": BillingInterval.MONTHLY,
        "amount": Decimal("300000"),
        "currency": Currency.TOMAN,
    },
}


class Command(BaseCommand):
    help = "Seed Billing prices for plans."

    def handle(self, *args, **options):
        for plan_code, definition in PLAN_PRICES.items():
            interval = definition["interval"]
            currency = definition["currency"]
            amount = definition["amount"]

            price = PlanPrice.objects.filter(
                plan_code=plan_code,
                interval=interval,
                currency=currency,
                is_active=True
            ).first()

            if price is None:
                PlanPrice.objects.create(
                    plan_code=plan_code,
                    interval=interval,
                    currency=currency,
                    amount=amount,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"Created active price for {plan_code}"))
            elif price.amount != amount:
                price.amount = amount
                price.save(update_fields=["amount"])
                self.stdout.write(self.style.SUCCESS(f"Updated active price for {plan_code} to {amount}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Price for {plan_code} already exists and is up to date"))

        self.stdout.write(self.style.SUCCESS("Billing prices seeded."))
