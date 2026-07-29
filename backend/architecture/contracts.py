"""Cross-domain architecture contracts.

Frozen Domain Contracts define which cross-domain database FKs are allowed.
Populate ALLOWED_CROSS_DOMAIN_FKS as Domains are implemented in B1+.

Each entry: (from_app, from_model, field_name, to_app)
"""

ALLOWED_CROSS_DOMAIN_FKS: set[tuple[str, str, str, str]] = set()

DOMAIN_APP_LABELS: set[str] = {
    "identity_access",
}
