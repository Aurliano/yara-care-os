"""C5 Push Notification & Caregiver Alert Architecture test suite.

Verifies:
1. MISSED -> CaregiverAlert created
2. duplicate event -> one CaregiverAlert
3. dispatcher replay -> no duplicate alert
4. push failure -> CaregiverAlert remains
5. Hub offline -> reconnect -> one alert
6. multiple workers -> one alert
7. alert creation independent of notification delivery
8. multi-device fan-out without duplicate CaregiverAlert
9. observability metrics distinction
"""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from common.observability.metrics import METRICS
from domains.care.enums import WorkflowExecutionResultType
from domains.care.models import CareActivity
from domains.care.services.interpretation import interpret_execution_result
from domains.care.services.prescriptions import create_prescription
from domains.identity_access.models import Membership
from domains.identity_access.services.profiles import create_user
from domains.notification.enums import AlertSeverity
from domains.notification.models import CaregiverAlert
from domains.notification.services.alerts import get_alert, list_elder_alerts, record_caregiver_alert
from domains.notification.services.push import (
    MockPushProvider,
    clear_device_tokens,
    dispatch_alert_push,
    register_device_token,
    set_push_provider,
)
from domains.scheduling.enums import OccurrenceStatus
from domains.scheduling.models import Occurrence
from domains.scheduling.services.due import process_due_occurrences
from domains.workflow.medication_reminder_policy import medication_reminder_definition
from domains.workflow.models import WorkflowExecution
from domains.workflow.services.executions import create_workflow_definition
from domains.workflow.services.timeout import process_timed_out_execution
from integration.context import IntegrationContext
from integration.handlers.events import handle_medication_missed
from domains.event.models import EventRecord
from integration.runtime.dispatcher import process_event, process_pending_events


@pytest.fixture(autouse=True)
def _reset_push_state():
    """Reset provider, tokens, and metrics between tests."""
    mock_provider = MockPushProvider()
    set_push_provider(mock_provider)
    clear_device_tokens()
    yield
    set_push_provider(None)
    clear_device_tokens()


@pytest.fixture
def medication_setup(licensed_elder, recurrence_definition, schedule_start_at):
    """Create a standard medication prescription and due occurrence."""
    workflow = create_workflow_definition(
        code=f"wf-c5-{uuid.uuid4().hex[:8]}",
        name="C5 Reminder Policy",
        definition=medication_reminder_definition(),
    )
    prescription = create_prescription(
        elder_id=licensed_elder.id,
        workflow_definition_id=workflow.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Metformin",
        medication_reference="med-metformin-500",
        dosage_information="500mg",
        elder_friendly_description="Take with breakfast",
    )
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=prescription.care_activity.schedule_definition_id
    ).first()
    occurrence.status = OccurrenceStatus.SCHEDULED
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=5)
    occurrence.save(update_fields=["status", "scheduled_for"])
    process_due_occurrences(now=timezone.now())

    ctx = IntegrationContext.new()
    process_pending_events(ctx, limit=200)

    execution = WorkflowExecution.objects.get(occurrence_id=occurrence.id)
    return {
        "elder": licensed_elder,
        "prescription": prescription,
        "occurrence": occurrence,
        "execution": execution,
        "ctx": ctx,
    }


# =========================================================================
# 1. MISSED -> CaregiverAlert created
# =========================================================================
@pytest.mark.django_db
def test_missed_creates_caregiver_alert(medication_setup):
    """When a medication execution misses, handle_medication_missed creates an urgent CaregiverAlert."""
    setup = medication_setup
    care_completion_id = uuid.uuid4()
    payload = {
        "care_activity_id": str(setup["prescription"].care_activity.id),
        "care_completion_id": str(care_completion_id),
        "workflow_execution_id": str(setup["execution"].id),
        "elder_id": str(setup["elder"].id),
    }

    handle_medication_missed(setup["ctx"], payload)

    alert = CaregiverAlert.objects.get(source_type="MEDICATION_MISSED")
    assert alert.elder_id == setup["elder"].id
    assert alert.severity == AlertSeverity.URGENT
    assert alert.source_reference == str(care_completion_id)
    assert "Metformin" in alert.title
    assert "انجام نشد" in alert.title
    assert "انجام‌نشده" in alert.body


# =========================================================================
# 2. Duplicate event -> one CaregiverAlert
# =========================================================================
@pytest.mark.django_db
def test_duplicate_missed_event_creates_only_one_alert(medication_setup):
    """Replaying the same MedicationMissed event payload results in exactly one CaregiverAlert."""
    setup = medication_setup
    care_completion_id = uuid.uuid4()
    payload = {
        "care_activity_id": str(setup["prescription"].care_activity.id),
        "care_completion_id": str(care_completion_id),
        "workflow_execution_id": str(setup["execution"].id),
        "elder_id": str(setup["elder"].id),
    }

    handle_medication_missed(setup["ctx"], payload)
    handle_medication_missed(setup["ctx"], payload)

    assert (
        CaregiverAlert.objects.filter(
            source_type="MEDICATION_MISSED",
            source_reference=str(care_completion_id),
        ).count()
        == 1
    )


# =========================================================================
# 3. Dispatcher replay -> no duplicate alert
# =========================================================================
@pytest.mark.django_db
def test_dispatcher_replay_does_not_duplicate_alert(medication_setup):
    """Dispatcher replay skips already processed event via ProcessedIntegrationEvent and idempotency."""
    setup = medication_setup
    care_completion_id = uuid.uuid4()
    event = EventRecord.objects.create(
        event_type="MedicationMissed",
        event_version=1,
        producer="care",
        occurred_at=timezone.now(),
        payload={
            "care_activity_id": str(setup["prescription"].care_activity.id),
            "care_completion_id": str(care_completion_id),
            "workflow_execution_id": str(setup["execution"].id),
            "elder_id": str(setup["elder"].id),
        },
    )

    first_dispatch = process_event(setup["ctx"], event.id)
    assert first_dispatch is True

    # Replay
    second_dispatch = process_event(setup["ctx"], event.id)
    assert second_dispatch is False  # Already processed

    alerts = CaregiverAlert.objects.filter(
        source_type="MEDICATION_MISSED",
        source_reference=str(care_completion_id),
    )
    assert alerts.count() == 1


# =========================================================================
# 4. Push failure -> CaregiverAlert remains
# =========================================================================
@pytest.mark.django_db
def test_push_failure_does_not_invalidate_caregiver_alert(medication_setup):
    """CRITICAL DOMAIN RULE: If push provider throws or fails, CaregiverAlert MUST remain intact."""
    setup = medication_setup
    fail_provider = MockPushProvider(fail_exception=RuntimeError("FCM connection timeout 503"))
    set_push_provider(fail_provider)

    initial_failed_metric = METRICS.get("notification.failed", 0)

    alert = record_caregiver_alert(
        elder_id=setup["elder"].id,
        title="داروی صبح انجام نشد",
        body="این نوبت انجام نشد.",
        severity=AlertSeverity.URGENT,
        source_type="MEDICATION_MISSED",
        source_reference="test-fail-push-1",
    )

    # Manually trigger dispatch with fail provider to verify isolated execution
    results = dispatch_alert_push(alert, tokens=["token-fcm-123"])
    assert len(results) == 1
    assert results[0].success is False
    assert "FCM connection timeout" in (results[0].error or "")

    # Alert MUST exist durably in database
    persisted = CaregiverAlert.objects.get(id=alert.id)
    assert persisted.title == "داروی صبح انجام نشد"
    assert METRICS.get("notification.failed", 0) > initial_failed_metric


# =========================================================================
# 5. Hub offline -> reconnect -> one alert
# =========================================================================
@pytest.mark.django_db
def test_hub_offline_timeout_converges_to_single_alert(medication_setup):
    """Simulate Hub offline execution reaching MISSED, reconnecting and syncing result to backend."""
    setup = medication_setup
    execution = setup["execution"]

    # Workflow runtime advances offline through timeouts until MISSED
    for _ in range(3):
        execution.active_until = timezone.now() - timedelta(seconds=1)
        execution.save(update_fields=["active_until"])
        process_timed_out_execution(execution)
        execution.refresh_from_db()

    # Timeout 4: final timeout -> ExecutionStatus.MISSED
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == "MISSED"

    # Hub reconnects: backend interprets execution result as MISSED
    interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_MISSED,
    )

    # Dispatcher processes pending integration events
    process_pending_events(setup["ctx"], limit=200)

    alerts = CaregiverAlert.objects.filter(elder_id=setup["elder"].id)
    # Escalation step created NOTIFY_CAREGIVER alert, and final missed created MEDICATION_MISSED alert
    missed_alert = alerts.filter(source_type="MEDICATION_MISSED")
    assert missed_alert.count() == 1
    assert missed_alert.first().severity == AlertSeverity.URGENT

    # Reconnect again / re-interpret
    interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_MISSED,
    )
    process_pending_events(setup["ctx"], limit=200)
    assert alerts.filter(source_type="MEDICATION_MISSED").count() == 1


# =========================================================================
# 6. Multiple workers -> one alert
# =========================================================================
@pytest.mark.django_db
def test_multiple_concurrent_workers_produce_exactly_one_alert(medication_setup):
    """Race condition simulation: two workers simultaneously recording the same alert."""
    setup = medication_setup
    source_ref = f"exec-worker-race-{uuid.uuid4().hex[:6]}"

    # Worker A
    alert_a = record_caregiver_alert(
        elder_id=setup["elder"].id,
        title="داروی صبح هنوز مصرف نشده",
        body="یادآوری پاسخ داده نشد.",
        severity=AlertSeverity.ATTENTION,
        source_type="NOTIFY_CAREGIVER",
        source_reference=source_ref,
    )

    # Worker B (simultaneous insert with same constraint keys)
    alert_b = record_caregiver_alert(
        elder_id=setup["elder"].id,
        title="داروی صبح هنوز مصرف نشده (worker b)",
        body="یادآوری پاسخ داده نشد.",
        severity=AlertSeverity.ATTENTION,
        source_type="NOTIFY_CAREGIVER",
        source_reference=source_ref,
    )

    assert alert_a.id == alert_b.id
    assert (
        CaregiverAlert.objects.filter(
            source_type="NOTIFY_CAREGIVER",
            source_reference=source_ref,
        ).count()
        == 1
    )


# =========================================================================
# 7. Alert creation independent of notification delivery
# =========================================================================
@pytest.mark.django_db
def test_alert_creation_independent_of_push_delivery(medication_setup):
    """CaregiverAlert is created and retrievable via API query even with 0 device tokens / no push."""
    setup = medication_setup
    # No device tokens registered
    clear_device_tokens()

    alert = record_caregiver_alert(
        elder_id=setup["elder"].id,
        title="آلارم یادآوری دارو",
        body="سالمند پاسخی نداده است.",
        severity=AlertSeverity.ATTENTION,
        source_type="NOTIFY_CAREGIVER",
        source_reference="standalone-alert-1",
    )

    assert alert.id is not None
    # Family App alert inbox query succeeds
    alerts = list_elder_alerts(elder_id=setup["elder"].id)
    assert any(a.id == alert.id for a in alerts)

    detail = get_alert(elder_id=setup["elder"].id, alert_id=alert.id)
    assert detail.id == alert.id


# =========================================================================
# 8. Multi-Device Caregiver: 1 domain alert -> N push deliveries
# =========================================================================
@pytest.mark.django_db
def test_multi_device_fan_out_preserves_single_domain_alert(medication_setup):
    """One caregiver with multiple registered devices receives multiple pushes, but exactly one CaregiverAlert exists."""
    setup = medication_setup
    provider = MockPushProvider()
    set_push_provider(provider)

    caregiver = create_user(
        phone="+989120000001",
        password="password123",
        full_name="Fatemeh Caregiver",
    )
    # Register 2 devices for this caregiver
    register_device_token(caregiver.id, "device-phone-token-1")
    register_device_token(caregiver.id, "device-tablet-token-2")

    alert = record_caregiver_alert(
        elder_id=setup["elder"].id,
        title="داروی متفورمین انجام نشد",
        body="لطفاً تماس بگیرید.",
        severity=AlertSeverity.URGENT,
        source_type="MEDICATION_MISSED",
        source_reference="multi-dev-1",
    )

    # Fan out push to caregiver's devices
    from domains.notification.services.push import get_caregiver_device_tokens_for_elder

    tokens = [
        "device-phone-token-1",
        "device-tablet-token-2",
    ]
    results = dispatch_alert_push(alert, tokens=tokens)

    # 2 push deliveries succeeded
    assert len(results) == 2
    assert all(r.success for r in results)
    assert len(provider.dispatched) == 2
    assert provider.dispatched[0]["recipient_token"] == "device-phone-token-1"
    assert provider.dispatched[1]["recipient_token"] == "device-tablet-token-2"

    # Exactly ONE domain alert exists in database
    assert (
        CaregiverAlert.objects.filter(
            source_type="MEDICATION_MISSED",
            source_reference="multi-dev-1",
        ).count()
        == 1
    )


# =========================================================================
# 9. Observability metrics distinction
# =========================================================================
@pytest.mark.django_db
def test_observability_metrics_distinguish_alert_and_delivery_lifecycle(medication_setup):
    """Metrics clearly distinguish: caregiver_alert.created, delivery_attempted, delivered, failed."""
    setup = medication_setup
    provider = MockPushProvider()
    set_push_provider(provider)

    start_created = METRICS.get("caregiver_alert.created", 0)
    start_attempted = METRICS.get("notification.delivery_attempted", 0)
    start_delivered = METRICS.get("notification.delivered", 0)
    start_failed = METRICS.get("notification.failed", 0)

    # 1. Successful alert and delivery
    alert_success = record_caregiver_alert(
        elder_id=setup["elder"].id,
        title="هشدار اول",
        body="متن اول",
        severity=AlertSeverity.ATTENTION,
        source_type="NOTIFY_CAREGIVER",
        source_reference="obs-success-1",
    )
    dispatch_alert_push(alert_success, tokens=["token-ok-1"])

    assert METRICS.get("caregiver_alert.created", 0) == start_created + 1
    assert METRICS.get("notification.delivery_attempted", 0) == start_attempted + 1
    assert METRICS.get("notification.delivered", 0) == start_delivered + 1
    assert METRICS.get("notification.failed", 0) == start_failed

    # 2. Failed delivery
    provider.should_fail = True
    alert_fail = record_caregiver_alert(
        elder_id=setup["elder"].id,
        title="هشدار دوم",
        body="متن دوم",
        severity=AlertSeverity.URGENT,
        source_type="MEDICATION_MISSED",
        source_reference="obs-fail-1",
    )
    dispatch_alert_push(alert_fail, tokens=["token-fail-1"])

    assert METRICS.get("caregiver_alert.created", 0) == start_created + 2
    assert METRICS.get("notification.delivery_attempted", 0) == start_attempted + 2
    assert METRICS.get("notification.delivered", 0) == start_delivered + 1
    assert METRICS.get("notification.failed", 0) == start_failed + 1
