"""Architecture tests for Licensing domain boundaries."""

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_licensing_cross_domain_fk_is_allowed() -> None:
    relations = collect_foreign_key_relations(app_labels={"licensing"})
    elder_fks = [r for r in relations if r.field_name == "elder"]
    assert len(elder_fks) == 1
    assert elder_fks[0].to_app == "identity_access"


def test_no_forbidden_licensing_cross_domain_fks() -> None:
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_identity_access_does_not_import_licensing() -> None:
    import importlib
    import pkgutil

    package = importlib.import_module("domains.identity_access")
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if "test" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "domains.licensing" not in content, f"{module_name} imports licensing"
