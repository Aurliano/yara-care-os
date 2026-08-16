"""Architecture tests for Communication domain boundaries."""

import importlib
import pkgutil

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_communication_cross_domain_fks_are_allowed():
    relations = collect_foreign_key_relations(app_labels={"communication"})
    cross_domain = [r for r in relations if r.from_app == "communication" and r.to_app != "communication"]
    allowed = {
        (r.from_app, r.from_model, r.field_name, r.to_app)
        for r in cross_domain
    }
    assert allowed.issubset(ALLOWED_CROSS_DOMAIN_FKS)


def test_communication_session_has_no_workflow_fk():
    relations = collect_foreign_key_relations(app_labels={"communication"})
    workflow_refs = [r for r in relations if r.to_app == "workflow"]
    assert workflow_refs == []


def test_no_forbidden_communication_cross_domain_fks():
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_communication_does_not_import_workflow_care_or_device():
    forbidden = (
        "domains.workflow",
        "domains.care",
        "domains.device",
        "domains.notification",
        "domains.synchronization",
    )
    package = importlib.import_module("domains.communication")
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
        assert "WorkflowExecution" not in content
        assert "skyroom.online" not in content
        assert "SKYROOM_API_KEY" not in content
        assert "SkyroomCommunicationProvider" not in content


def test_communication_session_has_no_provider_columns():
    from domains.communication.models import CommunicationSession

    field_names = {field.name.lower() for field in CommunicationSession._meta.get_fields()}
    assert "skyroom_room_id" not in field_names
    assert "skyroom_user_id" not in field_names
    assert "external_room_id" not in field_names


def test_infrastructure_is_not_a_domain_app():
    assert "infrastructure" not in DOMAIN_APP_LABELS

