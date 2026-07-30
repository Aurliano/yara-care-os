import uuid
from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from zoneinfo import ZoneInfo

from domains.event.models import EventRecord
from domains.identity_access.services.profiles import create_user
from domains.scheduling.enums import OccurrenceStatus, ScheduleExceptionType, ScheduleStatus
from domains.scheduling.identity import compute_occurrence_id
from domains.scheduling.models import Occurrence
from domains.scheduling.services.due import process_due_occurrences
from domains.scheduling.services.occurrences import generate_occurrences_for_schedule
from domains.scheduling.services.schedules import create_schedule


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, db) -> APIClient:
    user = create_user(
        phone="+989121111111",
        password="securepass123",
        full_name="Scheduling Tester",
    )
    api_client.force_authenticate(user=user)
    return api_client


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt


def _daily_schedule(**overrides):
    defaults = {
        "owner_reference": "care_activity:test-123",
        "recurrence_definition": {"type": "daily", "time": "08:00"},
        "timezone_name": "Asia/Tehran",
        "start_at": _aware(datetime(2026, 7, 1, 4, 30, tzinfo=ZoneInfo("UTC"))),
    }
    defaults.update(overrides)
    return create_schedule(**defaults)
