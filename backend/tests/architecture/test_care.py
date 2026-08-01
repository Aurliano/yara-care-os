"""Architecture tests for Care domain boundaries."""

import importlib
import pkgutil

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_care_cross_domain_fks_are_allowed():
    relations = collect_foreign_key_relations(app_labels={"care"})
    cross_domain = [r for r in relations if r.from_app == "care" and r.to_app != "care"]
    allowed = {
        (r.from_app, r.from_model, r.field_name, r.to_app)
        for r in cross_domain
    }
    assert allowed.issubset(ALLOWED_CROSS_DOMAIN_FKS)


def test_no_forbidden_care_cross_domain_fks():
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_care_does_not_import_licensing_device_communication():
    forbidden = (
        "domains.licensing",
        "domains.device",
        "domains.communication",
        "domains.notification",
        "domains.synchronization",
    )
    package = importlib.import_module("domains.care")
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if "test" in module_name or "migrations" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        for name in forbidden:
            assert name not in content, f"{module_name} imports {name}"


def test_workflow_and_scheduling_do_not_import_care():
    for domain in ("workflow", "scheduling"):
        package = importlib.import_module(f"domains.{domain}")
        for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            if "test" in module_name or "migrations" in module_name:
                continue
            module = importlib.import_module(module_name)
            source = getattr(module, "__file__", "") or ""
            if not source.endswith(".py"):
                continue
            with open(source, encoding="utf-8") as handle:
                content = handle.read()
            assert "domains.care" not in content, f"{module_name} imports care"
