"""Workflow hooks for authorization and lifecycle."""

from __future__ import annotations

from typing import Callable

ExecutionAccessHook = Callable[[object, object], bool]

_execution_access_hook: ExecutionAccessHook | None = None


def register_execution_access_hook(hook: ExecutionAccessHook) -> None:
    global _execution_access_hook
    _execution_access_hook = hook


def can_access_execution(user: object, execution: object) -> bool:
    if _execution_access_hook is None:
        return True
    return _execution_access_hook(user, execution)
