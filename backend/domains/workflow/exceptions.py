"""Workflow domain exceptions."""


class WorkflowError(Exception):
    """Base exception for Workflow domain errors."""


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow definition cannot be found."""


class ExecutionNotFoundError(WorkflowError):
    """Raised when a workflow execution cannot be found."""


class WorkflowBindingNotFoundError(WorkflowError):
    """Raised when schedule-to-workflow binding is missing."""


class InvalidExecutionStateError(WorkflowError):
    """Raised when an execution operation conflicts with current status."""


class InvalidEvidenceError(WorkflowError):
    """Raised when submitted evidence is not accepted by policy."""


class PostponeNotAllowedError(WorkflowError):
    """Raised when postpone violates workflow policy."""


class RetryNotAllowedError(WorkflowError):
    """Raised when retry violates workflow policy."""


class EscalationNotAllowedError(WorkflowError):
    """Raised when escalation is not permitted."""


class InvalidDefinitionError(WorkflowError):
    """Raised when workflow definition JSON is invalid."""
