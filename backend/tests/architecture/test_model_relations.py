from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import (
    collect_foreign_key_relations,
    find_cross_domain_relations,
)


def test_collect_foreign_key_relations_returns_list() -> None:
    relations = collect_foreign_key_relations()
    assert isinstance(relations, list)


def test_find_cross_domain_relations_with_no_domains() -> None:
    violations = find_cross_domain_relations(
        domain_apps=set(),
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []


def test_find_cross_domain_relations_respects_allowlist() -> None:
    """Helper logic is testable before real Domain models exist."""
    violations = find_cross_domain_relations(
        domain_apps={"care", "identity_access"},
        allowed_cross_domain_fks={
            ("care", "CareActivity", "elder", "identity_access"),
        },
    )
    assert violations == []
