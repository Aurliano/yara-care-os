"""Operational health and readiness probes."""

from __future__ import annotations

from datetime import timedelta
import logging

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from integration.models import ProcessedIntegrationEvent

logger = logging.getLogger("yara.integration")

_RESUMABLE_STATUSES = (
    "SYNCHRONIZATION_REQUESTED",
    "SESSION_STARTED",
    "PAYLOAD_RECEIVED",
    "SYNCHRONIZATION_RESUMED",
    "RETRY_SCHEDULED",
)


def _check_database() -> dict:
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — health probe must not raise
        logger.exception("Database connectivity health probe failed: %s", exc)
        return {"status": "error", "detail": "Database connectivity check failed."}


def check_migrations() -> dict:
    try:
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)
        if plan:
            pending_count = len(plan)
            logger.warning("Pending unapplied migrations detected: %d migration(s) pending.", pending_count)
            return {
                "status": "error",
                "detail": f"{pending_count} unapplied migration(s) pending.",
            }
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — health probe must not raise
        logger.exception("Migration readiness check failed: %s", exc)
        return {"status": "error", "detail": "Migration readiness check failed."}


def collect_readiness_status() -> dict:
    """Readiness probe checking database connectivity and pending migrations."""
    db_check = _check_database()
    if db_check["status"] == "error":
        return {
            "status": "unready",
            "checks": {
                "database": db_check,
                "migrations": {
                    "status": "unavailable",
                    "detail": "Database unreachable.",
                },
            },
        }

    migration_check = check_migrations()
    is_ready = migration_check["status"] == "ok"
    return {
        "status": "ready" if is_ready else "unready",
        "checks": {
            "database": db_check,
            "migrations": migration_check,
        },
    }


def _get_pending_outbox_count() -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM event_outbox WHERE status = %s", ["PENDING"])
        row = cursor.fetchone()
    return int(row[0]) if row else 0


def _count_stale_pending_outbox(*, older_than_minutes: int) -> int:
    threshold = timezone.now() - timedelta(minutes=older_than_minutes)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM event_outbox WHERE status = %s AND created_at <= %s",
            ["PENDING", threshold],
        )
        row = cursor.fetchone()
    return int(row[0]) if row else 0


def _count_active_synchronization_sessions() -> int:
    placeholders = ", ".join(["%s"] * len(_RESUMABLE_STATUSES))
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM synchronization_session WHERE status IN ({placeholders})",
            _RESUMABLE_STATUSES,
        )
        row = cursor.fetchone()
    return int(row[0]) if row else 0


def collect_health_status(*, stale_outbox_minutes: int = 15) -> dict:
    """Aggregate internal readiness checks for load balancers and ops."""
    db_check = _check_database()
    checks: dict[str, dict] = {
        "database": db_check,
    }

    if db_check["status"] == "error":
        checks["event_outbox"] = {
            "status": "unavailable",
            "pending": 0,
            "stale_pending": 0,
        }
        checks["integration_dispatcher"] = {
            "status": "unavailable",
            "processed_events": 0,
        }
        checks["synchronization"] = {
            "status": "unavailable",
            "active_sessions": 0,
        }
        return {
            "status": "error",
            "checked_at": timezone.now().isoformat(),
            "checks": checks,
        }

    pending_outbox = _get_pending_outbox_count()
    stale_outbox = _count_stale_pending_outbox(older_than_minutes=stale_outbox_minutes)
    checks["event_outbox"] = {
        "status": "degraded" if pending_outbox > 0 else "ok",
        "pending": pending_outbox,
        "stale_pending": stale_outbox,
    }

    processed_events = ProcessedIntegrationEvent.objects.count()
    checks["integration_dispatcher"] = {
        "status": "ok",
        "processed_events": processed_events,
    }

    active_sessions = _count_active_synchronization_sessions()
    checks["synchronization"] = {
        "status": "degraded" if active_sessions > 0 else "ok",
        "active_sessions": active_sessions,
    }

    overall = "ok"
    if any(check.get("status") == "degraded" for check in checks.values()):
        overall = "degraded"

    return {
        "status": overall,
        "checked_at": timezone.now().isoformat(),
        "checks": checks,
    }
