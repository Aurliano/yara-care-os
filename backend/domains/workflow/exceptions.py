"""Workflow domain exceptions."""


class WorkflowError(Exception):
    """Base exception for Workflow domain errors."""


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow definition cannot be found."""


class ExecutionNotFoundError(WorkflowError):
    """Raised when a workflow execution cannot be found."""


class WorkflowDefinitionConflictError(WorkflowError):
    """Raised when StartExecution is called with a conflicting workflow definition."""


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
