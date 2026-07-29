"""Cross-domain FK architecture checks (expanded in B1+)."""

from architecture.contracts import ALLOWED_CROSS_DOMAIN_FKS, DOMAIN_APP_LABELS
from architecture.model_relations import find_cross_domain_relations


def test_no_forbidden_cross_domain_foreign_keys() -> None:
    """Fail when a cross-domain FK is not allowed by Frozen Domain Contracts."""
    if not DOMAIN_APP_LABELS:
        return

    violations = find_cross_domain_relations(
        domain_apps=DOMAIN_APP_LABELS,
        allowed_cross_domain_fks=ALLOWED_CROSS_DOMAIN_FKS,
    )
    assert violations == [], (
        "Forbidden cross-domain FK relations detected:\n"
        + "\n".join(
            f"  {v.from_app}.{v.from_model}.{v.field_name} -> {v.to_app}.{v.to_model}"
            for v in violations
        )
    )
