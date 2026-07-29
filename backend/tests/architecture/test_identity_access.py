"""Architecture tests for Identity & Access domain boundaries."""

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import collect_foreign_key_relations, find_cross_domain_relations


def test_identity_access_relations_are_internal() -> None:
    relations = collect_foreign_key_relations(app_labels=DOMAIN_APP_LABELS)
    assert relations, "Expected Identity & Access models to define relations."

    for relation in relations:
        assert relation.from_app in DOMAIN_APP_LABELS
        assert relation.to_app in DOMAIN_APP_LABELS


def test_identity_access_has_no_cross_domain_fk_violations() -> None:
    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == []
