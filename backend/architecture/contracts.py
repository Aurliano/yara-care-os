"""Cross-domain architecture contracts."""

ALLOWED_CROSS_DOMAIN_FKS: set[tuple[str, str, str, str]] = {
    ("licensing", "License", "elder", "identity_access"),
    ("workflow", "WorkflowExecution", "occurrence", "scheduling"),
    ("care", "CareActivity", "elder", "identity_access"),
    ("care", "CareActivity", "schedule_definition", "scheduling"),
    ("care", "CareActivity", "workflow_definition", "workflow"),
    ("device", "DeviceAssignment", "elder", "identity_access"),
    ("communication", "Contact", "elder", "identity_access"),
    ("communication", "CommunicationSession", "elder", "identity_access"),
}

DOMAIN_APP_LABELS: set[str] = {
    "identity_access",
    "licensing",
    "event",
    "scheduling",
    "workflow",
    "care",
    "device",
    "communication",
}
