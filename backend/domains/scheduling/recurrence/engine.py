"""Centralized recurrence evaluation owned exclusively by Scheduling."""

from __future__ import annotations

import re
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

TIME_FORMAT_REGEX = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


@dataclass(frozen=True, slots=True)
class RecurrenceSlot:
    """A logical occurrence slot before exceptions are applied."""

    original_time: datetime  # UTC-aware canonical instant for the slot


def parse_local_time(value: str) -> time:
    if not isinstance(value, str):
        raise InvalidRecurrenceDefinitionError("time must be a string in HH:MM format.")
    clean = value.strip()
    if not TIME_FORMAT_REGEX.match(clean):
        raise InvalidRecurrenceDefinitionError(f"Invalid time format '{value}'. Must use 24-hour HH:MM format.")
    parts = clean.split(":")
    hour, minute = int(parts[0]), int(parts[1])
    return time(hour=hour, minute=minute)


def extract_and_validate_times(recurrence_definition: dict[str, Any], required: bool = True) -> list[str]:
    """Validate, deduplicate, and deterministically sort time slots in HH:MM format."""
    if "times" in recurrence_definition:
        raw_times = recurrence_definition["times"]
        if not isinstance(raw_times, list):
            raise InvalidRecurrenceDefinitionError("times must be a list of HH:MM strings.")
        if len(raw_times) == 0:
            if required:
                raise InvalidRecurrenceDefinitionError("times cannot be empty for recurring schedule.")
            return []

        cleaned: list[str] = []
        for item in raw_times:
            if not isinstance(item, str):
                raise InvalidRecurrenceDefinitionError("Each time in times must be an HH:MM string.")
            t_str = item.strip()
            if not TIME_FORMAT_REGEX.match(t_str):
                raise InvalidRecurrenceDefinitionError(
                    f"Invalid time format '{item}'. Must use 24-hour HH:MM format (00:00 to 23:59)."
                )
            cleaned.append(t_str)

        if len(set(cleaned)) != len(cleaned):
            raise InvalidRecurrenceDefinitionError("Duplicate times are not allowed.")

        return sorted(cleaned)

    if "time" in recurrence_definition:
        raw_time = recurrence_definition["time"]
        if not isinstance(raw_time, str):
            raise InvalidRecurrenceDefinitionError("time must be a string in HH:MM format.")
        t_str = raw_time.strip()
        if not TIME_FORMAT_REGEX.match(t_str):
            raise InvalidRecurrenceDefinitionError(
                f"Invalid time format '{raw_time}'. Must use 24-hour HH:MM format (00:00 to 23:59)."
            )
        return [t_str]

    if required:
        raise InvalidRecurrenceDefinitionError("Recurrence definition requires 'time' or 'times'.")
    return []


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
    if recurrence_type in {"every_n_hours"} or (
        recurrence_type == "interval" and recurrence_definition.get("unit") == "hours"
    ):
        raise InvalidRecurrenceDefinitionError("Hourly interval recurrence is not supported in MVP.")

    if recurrence_type not in {"once", "daily", "weekly", "specific_days", "every_n_days", "interval"}:
        raise InvalidRecurrenceDefinitionError(
            "type must be one of: once, daily, specific_days, every_n_days."
        )

    if recurrence_type == "daily":
        extract_and_validate_times(recurrence_definition, required=True)

    elif recurrence_type in {"weekly", "specific_days"}:
        days = recurrence_definition.get("days")
        if not days or not isinstance(days, list) or len(days) == 0:
            raise InvalidRecurrenceDefinitionError("specific_days/weekly recurrence requires days.")
        for day in days:
            if day not in WEEKDAY_MAP:
                raise InvalidRecurrenceDefinitionError(f"Unsupported weekday: {day}")
        extract_and_validate_times(recurrence_definition, required=True)

    elif recurrence_type in {"every_n_days", "interval"}:
        if recurrence_type == "interval" and recurrence_definition.get("unit") != "days":
            raise InvalidRecurrenceDefinitionError("interval recurrence in MVP requires unit 'days'.")
        every = recurrence_definition.get("every")
        if not isinstance(every, int) or isinstance(every, bool) or every <= 0:
            raise InvalidRecurrenceDefinitionError("every_n_days recurrence requires positive integer every.")
        extract_and_validate_times(recurrence_definition, required=True)

    elif recurrence_type == "once":
        if "time" in recurrence_definition or "times" in recurrence_definition:
            times = extract_and_validate_times(recurrence_definition, required=False)
            if len(times) > 1:
                raise InvalidRecurrenceDefinitionError("once recurrence does not support multiple time slots.")


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

    sorted_times = extract_and_validate_times(recurrence_definition, required=True)
    local_start = _localize_instant(start_at, tz)
    current_day = max(local_start.date(), _localize_instant(effective_start, tz).date())
    end_day = _localize_instant(effective_end, tz).date()

    while current_day <= end_day:
        if recurrence_type == "daily":
            include_day = current_day >= local_start.date()
        elif recurrence_type in {"weekly", "specific_days"}:
            day_code = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][current_day.weekday()]
            include_day = day_code in recurrence_definition["days"] and current_day >= local_start.date()
        elif recurrence_type in {"every_n_days", "interval"}:
            every = recurrence_definition["every"]
            days_diff = (current_day - local_start.date()).days
            include_day = current_day >= local_start.date() and (days_diff >= 0) and (days_diff % every == 0)
        else:
            include_day = False

        if include_day:
            for t_str in sorted_times:
                slot_time = parse_local_time(t_str)
                local_dt = datetime.combine(current_day, slot_time, tzinfo=tz)
                slot = _to_utc_slot(local_dt, tz)
                if effective_start <= slot.original_time <= effective_end:
                    yield slot

        current_day += timedelta(days=1)

