"""Hooks for cross-domain lifecycle events on occurrences and schedules."""

from __future__ import annotations

import uuid
from typing import Callable

PreOccurrenceHook = Callable[[uuid.UUID], None]
PostOccurrenceHook = Callable[[uuid.UUID], None]

_pre_skip_hooks: list[PreOccurrenceHook] = []
_post_skip_hooks: list[PostOccurrenceHook] = []
_pre_reschedule_hooks: list[PreOccurrenceHook] = []
_post_reschedule_hooks: list[PostOccurrenceHook] = []


def register_pre_skip_hook(hook: PreOccurrenceHook) -> None:
    if hook not in _pre_skip_hooks:
        _pre_skip_hooks.append(hook)


def register_post_skip_hook(hook: PostOccurrenceHook) -> None:
    if hook not in _post_skip_hooks:
        _post_skip_hooks.append(hook)


def register_pre_reschedule_hook(hook: PreOccurrenceHook) -> None:
    if hook not in _pre_reschedule_hooks:
        _pre_reschedule_hooks.append(hook)


def register_post_reschedule_hook(hook: PostOccurrenceHook) -> None:
    if hook not in _post_reschedule_hooks:
        _post_reschedule_hooks.append(hook)


def run_pre_skip_hooks(occurrence_id: uuid.UUID) -> None:
    for hook in _pre_skip_hooks:
        hook(occurrence_id)


def run_post_skip_hooks(occurrence_id: uuid.UUID) -> None:
    for hook in _post_skip_hooks:
        hook(occurrence_id)


def run_pre_reschedule_hooks(occurrence_id: uuid.UUID) -> None:
    for hook in _pre_reschedule_hooks:
        hook(occurrence_id)


def run_post_reschedule_hooks(occurrence_id: uuid.UUID) -> None:
    for hook in _post_reschedule_hooks:
        hook(occurrence_id)


ScheduleAccessHook = Callable[[object, object], bool]
OccurrenceAccessHook = Callable[[object, object], bool]

_schedule_access_hook: ScheduleAccessHook | None = None
_occurrence_access_hook: OccurrenceAccessHook | None = None


def register_schedule_access_hook(hook: ScheduleAccessHook) -> None:
    global _schedule_access_hook
    _schedule_access_hook = hook


def register_occurrence_access_hook(hook: OccurrenceAccessHook) -> None:
    global _occurrence_access_hook
    _occurrence_access_hook = hook


def can_access_schedule(user: object, schedule: object) -> bool:
    if _schedule_access_hook is None:
        return True
    return _schedule_access_hook(user, schedule)


def can_access_occurrence(user: object, occurrence: object) -> bool:
    if _occurrence_access_hook is None:
        return True
    return _occurrence_access_hook(user, occurrence)

