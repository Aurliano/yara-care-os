"""Workflow definition parsing and validation."""

from __future__ import annotations

from typing import Any

from domains.workflow.enums import ActionType, EvidenceType
from domains.workflow.exceptions import InvalidDefinitionError


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InvalidDefinitionError(f"{field} must be an object.")
    return value


def validate_workflow_definition(definition: dict[str, Any]) -> dict[str, Any]:
    initial_action = _require_dict(definition.get("initial_action"), "initial_action")
    action_type = initial_action.get("type")
    if action_type not in ActionType.values:
        raise InvalidDefinitionError("initial_action.type is invalid.")

    policy = _require_dict(definition.get("confirmation_policy"), "confirmation_policy")
    accepted = policy.get("accepted_evidence_types", [])
    if not isinstance(accepted, list) or not accepted:
        raise InvalidDefinitionError("confirmation_policy.accepted_evidence_types is required.")
    for evidence_type in accepted:
        if evidence_type not in EvidenceType.values:
            raise InvalidDefinitionError(f"Unsupported evidence type: {evidence_type}")

    if "step_timeout_seconds" not in definition:
        raise InvalidDefinitionError("step_timeout_seconds is required.")

    return definition


def get_initial_action(definition: dict[str, Any]) -> dict[str, Any]:
    return _require_dict(definition["initial_action"], "initial_action")


def get_step_timeout_seconds(definition: dict[str, Any]) -> int:
    return int(definition["step_timeout_seconds"])


def get_retry_policy(definition: dict[str, Any]) -> dict[str, Any] | None:
    retry = definition.get("retry")
    return _require_dict(retry, "retry") if retry else None


def get_postpone_policy(definition: dict[str, Any]) -> dict[str, Any] | None:
    postpone = definition.get("postpone")
    return _require_dict(postpone, "postpone") if postpone else None


def get_escalation_steps(definition: dict[str, Any]) -> list[dict[str, Any]]:
    steps = definition.get("escalation_steps", [])
    if not isinstance(steps, list):
        raise InvalidDefinitionError("escalation_steps must be a list.")
    return steps


def get_accepted_evidence_types(definition: dict[str, Any]) -> set[str]:
    policy = _require_dict(definition["confirmation_policy"], "confirmation_policy")
    return set(policy["accepted_evidence_types"])
