"""Architecture tests for Billing domain boundaries."""

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_billing_has_no_cross_domain_fks() -> None:
    relations = collect_foreign_key_relations(app_labels={"billing"})
    cross_fks = [r for r in relations if r.to_app != "billing"]
    assert cross_fks == [], f"Billing should have zero cross-domain FKs (use raw UUIDs), found: {cross_fks}"


def test_no_forbidden_billing_cross_domain_fks() -> None:
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_billing_does_not_import_vendor_payment_sdks() -> None:
    import importlib
    import pkgutil

    package = importlib.import_module("domains.billing")
    forbidden_tokens = ["stripe", "zarinpal", "requests", "httpx", "urllib3"]
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read().lower()
        for token in forbidden_tokens:
            assert f"import {token}" not in content and f"from {token}" not in content, (
                f"{module_name} directly imports forbidden vendor/transport token '{token}'"
            )
