"""Cross-domain architecture contracts."""

ALLOWED_CROSS_DOMAIN_FKS: set[tuple[str, str, str, str]] = {
    ("licensing", "License", "elder", "identity_access"),
    ("workflow", "WorkflowExecution", "occurrence", "scheduling"),
}

DOMAIN_APP_LABELS: set[str] = {
    "identity_access",
    "licensing",
    "event",
    "scheduling",
    "workflow",
}
