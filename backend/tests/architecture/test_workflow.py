"""Architecture tests for Workflow domain boundaries."""

import importlib
import pkgutil

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_workflow_cross_domain_fk_to_scheduling_is_allowed():
    relations = collect_foreign_key_relations(app_labels={"workflow"})
    occurrence_fks = [r for r in relations if r.field_name == "occurrence"]
    assert len(occurrence_fks) == 1
    assert occurrence_fks[0].to_app == "scheduling"


def test_no_forbidden_workflow_cross_domain_fks():
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_workflow_does_not_import_care_device_communication():
    forbidden = (
        "domains.care",
        "domains.device",
        "domains.communication",
        "domains.notification",
        "domains.synchronization",
    )
    package = importlib.import_module("domains.workflow")
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


def test_scheduling_and_event_do_not_import_workflow():
    for domain in ("scheduling", "event"):
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
            assert "domains.workflow" not in content, f"{module_name} imports workflow"
