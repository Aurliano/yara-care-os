"""Licensing domain hooks and extension points."""

from typing import Callable

_paid_plan_checker: Callable[[str], bool] | None = None


def register_paid_plan_checker(checker: Callable[[str], bool]) -> None:
    """Register an external checker (e.g. from payment/billing) to identify paid plans."""
    global _paid_plan_checker
    _paid_plan_checker = checker


def is_paid_plan(plan_code: str) -> bool:
    """Return True if plan_code represents a paid tier requiring payment settlement."""
    if _paid_plan_checker is not None:
        return _paid_plan_checker(plan_code)
    # Default fallback: BASIC and FREE are non-paid; all other plans require payment settlement
    return plan_code not in {"BASIC", "FREE"}
