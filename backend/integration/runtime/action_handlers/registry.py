"""Extensible workflow action handler registry."""

from __future__ import annotations

from typing import Any, Protocol

from integration.context import IntegrationContext
from integration.observability import logging as integration_logging
from integration.observability.metrics import increment


class ActionHandler(Protocol):
    action_type: str

    def handle(self, ctx: IntegrationContext, *, payload: dict[str, Any]) -> None: ...


class ActionHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, handler: ActionHandler) -> None:
        self._handlers[handler.action_type] = handler

    def dispatch(self, ctx: IntegrationContext, *, payload: dict[str, Any]) -> None:
        action = payload.get("current_action") or payload.get("action") or {}
        action_type = action.get("type") or payload.get("action_type")
        if not action_type:
            integration_logging.log_orchestration_step(ctx, "action_dispatch_skipped_no_type")
            return
        handler = self._handlers.get(action_type)
        if handler is None:
            integration_logging.log_orchestration_step(ctx, "action_dispatch_unhandled", action_type=action_type)
            increment("integration.action.unhandled")
            return
        integration_logging.log_orchestration_step(ctx, "action_dispatch", action_type=action_type)
        handler.handle(ctx, payload=payload)
        increment("integration.action.dispatched")


REGISTRY = ActionHandlerRegistry()
