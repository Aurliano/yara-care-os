"""Architecture tests for Event domain boundaries."""

import importlib
import pkgutil

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_event_has_no_cross_domain_foreign_keys():
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_event_record_relations_are_internal():
    relations = collect_foreign_key_relations(app_labels={"event"})
    cross_domain = [r for r in relations if r.to_app != "event"]
    assert cross_domain == []


def test_event_does_not_import_other_domains():
    package = importlib.import_module("domains.event")
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if "test" in module_name or "migrations" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "domains.identity_access" not in content, f"{module_name} imports identity_access"
        assert "domains.licensing" not in content, f"{module_name} imports licensing"
