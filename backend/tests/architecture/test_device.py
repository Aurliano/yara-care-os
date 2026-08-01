"""Architecture tests for Device domain boundaries."""

import importlib
import pkgutil

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_device_cross_domain_fk_to_identity_is_allowed():
    relations = collect_foreign_key_relations(app_labels={"device"})
    elder_fks = [r for r in relations if r.field_name == "elder"]
    assert len(elder_fks) == 1
    assert elder_fks[0].to_app == "identity_access"


def test_device_command_has_no_workflow_fk():
    relations = collect_foreign_key_relations(app_labels={"device"})
    workflow_refs = [r for r in relations if r.to_app == "workflow"]
    assert workflow_refs == []


def test_no_forbidden_device_cross_domain_fks():
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_device_does_not_import_workflow_or_care():
    forbidden = (
        "domains.workflow",
        "domains.care",
        "domains.communication",
        "domains.notification",
        "domains.synchronization",
    )
    package = importlib.import_module("domains.device")
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
        assert "WorkflowExecution" not in content, f"{module_name} references WorkflowExecution model"
