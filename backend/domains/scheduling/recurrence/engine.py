"""Centralized recurrence evaluation owned exclusively by Scheduling."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from domains.scheduling.exceptions import InvalidRecurrenceDefinitionError

WEEKDAY_MAP = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
}


@dataclass(frozen=True, slots=True)
class RecurrenceSlot:
  """A logical occurrence slot before exceptions are applied."""

  original_time: datetime  # UTC-aware canonical instant for the slot


def parse_local_time(value: str) -> time:
    parts = value.split(":")
    if len(parts) != 2:
        raise InvalidRecurrenceDefinitionError("time must use HH:MM format.")
    hour, minute = int(parts[0]), int(parts[1])
    return time(hour=hour, minute=minute)


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise InvalidRecurrenceDefinitionError("Datetime values must be timezone-aware.")
    return value.astimezone(ZoneInfo("UTC")).replace(microsecond=0)


def _localize_instant(value: datetime, tz: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def _to_utc_slot(local_dt: datetime, tz: ZoneInfo) -> RecurrenceSlot:
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=tz)
    return RecurrenceSlot(original_time=local_dt.astimezone(ZoneInfo("UTC")).replace(microsecond=0))


def validate_recurrence_definition(recurrence_definition: dict[str, Any]) -> None:
    recurrence_type = recurrence_definition.get("type")
    if recurrence_type not in {"once", "daily", "weekly", "interval"}:
        raise InvalidRecurrenceDefinitionError("type must be one of: once, daily, weekly, interval.")

    if recurrence_type in {"daily", "weekly"}:
        if "time" not in recurrence_definition:
            raise InvalidRecurrenceDefinitionError("daily/weekly recurrence requires time.")
        parse_local_time(recurrence_definition["time"])

    if recurrence_type == "weekly":
        days = recurrence_definition.get("days")
        if not days:
            raise InvalidRecurrenceDefinitionError("weekly recurrence requires days.")
        for day in days:
            if day not in WEEKDAY_MAP:
                raise InvalidRecurrenceDefinitionError(f"Unsupported weekday: {day}")

    if recurrence_type == "interval":
        if recurrence_definition.get("unit") not in {"hours", "days"}:
            raise InvalidRecurrenceDefinitionError("interval recurrence requires unit hours or days.")
        every = recurrence_definition.get("every")
        if not isinstance(every, int) or every <= 0:
            raise InvalidRecurrenceDefinitionError("interval recurrence requires positive integer every.")


def iter_recurrence_slots(
    *,
    recurrence_definition: dict[str, Any],
    timezone_name: str,
    start_at: datetime,
    end_at: datetime | None,
    range_start: datetime,
    range_end: datetime,
) -> Iterator[RecurrenceSlot]:
    """Yield logical recurrence slots within [range_start, range_end]."""
    validate_recurrence_definition(recurrence_definition)
    tz = ZoneInfo(timezone_name)
    start_at_utc = _ensure_aware_utc(start_at)
    range_start_utc = _ensure_aware_utc(range_start)
    range_end_utc = _ensure_aware_utc(range_end)
    schedule_end_utc = _ensure_aware_utc(end_at) if end_at is not None else None

    effective_start = max(start_at_utc, range_start_utc)
    effective_end = min(range_end_utc, schedule_end_utc) if schedule_end_utc else range_end_utc
    if effective_start > effective_end:
        return

    recurrence_type = recurrence_definition["type"]
    if recurrence_type == "once":
        if start_at_utc <= effective_end and start_at_utc >= effective_start:
            yield RecurrenceSlot(original_time=start_at_utc)
        return

    if recurrence_type == "interval":
        yield from _iter_interval_slots(
            recurrence_definition=recurrence_definition,
            start_at_utc=start_at_utc,
            effective_start=effective_start,
            effective_end=effective_end,
        )
        return

    local_time = parse_local_time(recurrence_definition["time"])
    local_start = _localize_instant(start_at, tz)
    current_day = max(local_start.date(), _localize_instant(effective_start, tz).date())
    end_day = _localize_instant(effective_end, tz).date()

    while current_day <= end_day:
        if recurrence_type == "daily":
            include_day = current_day >= local_start.date()
        else:
            day_code = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][current_day.weekday()]
            include_day = day_code in recurrence_definition["days"] and current_day >= local_start.date()

        if include_day:
            local_dt = datetime.combine(current_day, local_time, tzinfo=tz)
            slot = _to_utc_slot(local_dt, tz)
            if effective_start <= slot.original_time <= effective_end:
                yield slot

        current_day += timedelta(days=1)


def _iter_interval_slots(
    *,
    recurrence_definition: dict[str, Any],
    start_at_utc: datetime,
    effective_start: datetime,
    effective_end: datetime,
) -> Iterator[RecurrenceSlot]:
    every = recurrence_definition["every"]
    unit = recurrence_definition["unit"]
    delta = timedelta(hours=every) if unit == "hours" else timedelta(days=every)

    current = start_at_utc
    while current < effective_start:
        current += delta

    while current <= effective_end:
        yield RecurrenceSlot(original_time=current)
        current += delta
