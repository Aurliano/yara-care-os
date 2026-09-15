import pytest
from io import StringIO
from django.core.management import call_command
from domains.billing.models import PlanPrice
from domains.billing.enums import BillingInterval, Currency

@pytest.mark.django_db
def test_seed_billing_idempotency():
    # Initial state
    assert PlanPrice.objects.count() == 0

    # First run
    out1 = StringIO()
    call_command("seed_billing", stdout=out1)
    
    assert PlanPrice.objects.count() == 3
    
    # Check that prices are created correctly
    basic_price = PlanPrice.objects.get(plan_code="BASIC")
    assert basic_price.amount == 0
    assert basic_price.currency == Currency.TOMAN
    assert basic_price.interval == BillingInterval.MONTHLY
    
    # Second run
    out2 = StringIO()
    call_command("seed_billing", stdout=out2)
    
    # Ensure no duplicates were created
    assert PlanPrice.objects.count() == 3
    assert "already exists and is up to date" in out2.getvalue()

