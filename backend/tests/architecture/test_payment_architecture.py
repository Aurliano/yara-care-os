"""Architecture boundary tests for Payment, Billing, and Licensing."""

import importlib
import pkgutil


def test_billing_does_not_import_infrastructure_payment():
    package = importlib.import_module("domains.billing")
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "infrastructure.payment" not in content, (
            f"{module_name} directly imports infrastructure.payment"
        )


def test_licensing_does_not_import_infrastructure_payment():
    package = importlib.import_module("domains.licensing")
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "infrastructure.payment" not in content, (
            f"{module_name} directly imports infrastructure.payment"
        )


def test_billing_does_not_import_licensing():
    package = importlib.import_module("domains.billing")
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "domains.licensing" not in content, (
            f"{module_name} directly imports domains.licensing"
        )


def test_licensing_does_not_import_billing():
    package = importlib.import_module("domains.licensing")
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "domains.billing" not in content, (
            f"{module_name} directly imports domains.billing"
        )


def test_infrastructure_payment_does_not_import_domains():
    package = importlib.import_module("infrastructure.payment")
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "domains." not in content, (
            f"{module_name} in infrastructure.payment imports domain package"
        )


def test_application_payments_does_not_import_vendor_payment_sdks():
    package = importlib.import_module("application.payments")
    forbidden_tokens = ["stripe", "zarinpal", "requests", "httpx", "urllib3"]
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read().lower()
        for token in forbidden_tokens:
            assert (
                f"import {token}" not in content and f"from {token}" not in content
            ), f"{module_name} directly imports forbidden vendor token '{token}'"
