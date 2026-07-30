"""Approved evidence type identifiers for MVP ConfirmationPolicy configuration.

These are policy reference strings, not a closed global enum on Workflow core.
ConfirmationPolicy may reference only identifiers backed by frozen contracts.
"""

APPROVED_EVIDENCE_TYPES: frozenset[str] = frozenset(
    {
        "HUB_CONFIRMATION",
        "COMPARTMENT_CLOSED",
        "COMMUNICATION_SESSION_ENDED",
    }
)


def is_approved_evidence_type(value: str) -> bool:
    return value in APPROVED_EVIDENCE_TYPES
