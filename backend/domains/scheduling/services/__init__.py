"""Public Scheduling domain service interface.

Contract mapping (Frozen Scheduling Domain Contract V1.1):

Commands:
- CreateSchedule -> create_schedule
- UpdateSchedule -> update_schedule
- PauseSchedule -> pause_schedule
- ResumeSchedule -> resume_schedule
- CancelSchedule -> cancel_schedule
- AddScheduleException -> add_schedule_exception
- CancelOccurrence -> cancel_occurrence
- SkipOccurrence -> skip_occurrence

Queries:
- GetSchedule -> get_schedule
- GetNextOccurrence -> get_next_occurrence
- GetUpcomingOccurrences -> get_upcoming_occurrences
- GetOccurrencesBetween -> get_occurrences_between
- GetOccurrence -> get_occurrence
"""

from domains.scheduling.services.due import mark_occurrence_due, process_due_occurrences
from domains.scheduling.services.occurrences import (
    cancel_occurrence,
    generate_occurrences_for_schedule,
    get_next_occurrence,
    get_occurrence,
    get_occurrences_between,
    get_upcoming_occurrences,
    skip_occurrence,
)
from domains.scheduling.services.schedules import (
    add_schedule_exception,
    cancel_schedule,
    create_schedule,
    get_schedule,
    pause_schedule,
    resume_schedule,
    update_schedule,
)

__all__ = [
    "add_schedule_exception",
    "cancel_occurrence",
    "cancel_schedule",
    "create_schedule",
    "generate_occurrences_for_schedule",
    "get_next_occurrence",
    "get_occurrence",
    "get_occurrences_between",
    "get_schedule",
    "get_upcoming_occurrences",
    "mark_occurrence_due",
    "pause_schedule",
    "process_due_occurrences",
    "resume_schedule",
    "skip_occurrence",
    "update_schedule",
]
