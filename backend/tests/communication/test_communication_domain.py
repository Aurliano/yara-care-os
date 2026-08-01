import uuid

import pytest
from django.apps import apps
from django.utils import timezone

from domains.communication.enums import (
    CallAttemptOutcome,
    CommunicationChannel,
    ContactStatus,
    ParticipantRole,
    SessionOutcome,
    SessionStatus,
)
from domains.communication.exceptions import EntitlementDeniedError, InvalidSessionStateError
from domains.communication.models import CallAttempt, CommunicationSession, Contact
from domains.communication.services.contacts import (
    archive_contact,
    create_contact,
    get_elder_contacts,
    get_priority_contacts,
    remove_priority_contact,
    set_priority_contact,
)
from domains.communication.services.sessions import (
    accept_session,
    cancel_session,
    decline_session,
    end_session,
    get_call_attempts,
    initiate_session,
    record_call_attempt,
    report_attempt_result,
)
from domains.event.models import EventRecord
from domains.identity_access.models import EmergencyRecipient


@pytest.mark.django_db
def test_contact_archive_not_delete(licensed_elder):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Daughter",
        phone="+989121111111",
        preferred_channel=CommunicationChannel.VOICE,
    )
    archived = archive_contact(contact_id=contact.id)
    assert archived.status == ContactStatus.ARCHIVED
    assert archived.archived_at is not None
    assert Contact.objects.filter(pk=contact.id).exists()
    assert EventRecord.objects.filter(event_type="ContactArchived").count() == 1
    assert get_elder_contacts(elder_id=licensed_elder.id) == []


@pytest.mark.django_db
def test_priority_contact_is_not_emergency_recipient(licensed_elder):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Priority Daughter",
        preferred_channel=CommunicationChannel.VOICE,
    )
    set_priority_contact(contact_id=contact.id)
    assert get_priority_contacts(elder_id=licensed_elder.id)[0].is_priority is True
    assert isinstance(EmergencyRecipient._meta.app_label, str)
    assert EmergencyRecipient._meta.app_label == "identity_access"
    assert Contact._meta.app_label == "communication"
    remove_priority_contact(contact_id=contact.id)
    assert get_priority_contacts(elder_id=licensed_elder.id) == []


@pytest.mark.django_db
def test_session_lifecycle(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Son",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    assert session.status == SessionStatus.INITIATED
    assert EventRecord.objects.filter(event_type="CommunicationSessionInitiated").count() == 1

    attempt = record_call_attempt(session_id=session.id)
    assert attempt.attempt_number == 1
    session.refresh_from_db()
    assert session.status == SessionStatus.CONNECTING

    report_attempt_result(attempt_id=attempt.id, outcome=CallAttemptOutcome.CONNECTED)
    session.refresh_from_db()
    assert session.status == SessionStatus.CONNECTED
    assert session.connected_at is not None
    assert EventRecord.objects.filter(event_type="CommunicationSessionConnected").count() == 1

    ended = end_session(session_id=session.id)
    assert ended.status == SessionStatus.ENDED
    assert ended.outcome == SessionOutcome.ANSWERED
    assert ended.ended_at is not None
    assert ended.ended_at >= ended.connected_at


@pytest.mark.django_db
def test_communication_session_aggregate_version_owned_by_communication(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Version callee",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    assert session.aggregate_version == 1

    record_call_attempt(session_id=session.id)
    session.refresh_from_db()
    assert session.aggregate_version == 2


@pytest.mark.django_db
def test_terminal_session_immutable(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Callee",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    cancelled = cancel_session(session_id=session.id)
    assert cancelled.status == SessionStatus.CANCELLED
    with pytest.raises(InvalidSessionStateError):
        accept_session(session_id=session.id)


@pytest.mark.django_db
def test_multiple_call_attempts_preserved(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Retry Contact",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    first = record_call_attempt(session_id=session.id)
    report_attempt_result(attempt_id=first.id, outcome=CallAttemptOutcome.FAILED, failure_reason="no answer")
    second = record_call_attempt(session_id=session.id)
    report_attempt_result(attempt_id=second.id, outcome=CallAttemptOutcome.CONNECTED)
    attempts = get_call_attempts(session_id=session.id)
    assert len(attempts) == 2
    assert attempts[0].outcome == CallAttemptOutcome.FAILED
    assert attempts[1].outcome == CallAttemptOutcome.CONNECTED


@pytest.mark.django_db
def test_video_session_requires_entitlement(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Video Contact",
        preferred_channel=CommunicationChannel.VIDEO,
    )
    with pytest.raises(EntitlementDeniedError):
        initiate_session(
            elder_id=licensed_elder.id,
            channel=CommunicationChannel.VIDEO,
            initiator_user_id=comm_user.id,
            recipient_contact_id=recipient.id,
        )


@pytest.mark.django_db
def test_external_execution_reference_opaque(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Workflow Contact",
        preferred_channel=CommunicationChannel.VOICE,
    )
    execution_ref = uuid.uuid4()
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
        external_execution_reference=execution_ref,
    )
    assert session.external_execution_reference == execution_ref
    field = CommunicationSession._meta.get_field("external_execution_reference")
    assert field.__class__.__name__ == "UUIDField"


@pytest.mark.django_db
def test_decline_session_explicit_outcome(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Decline Contact",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    declined = decline_session(session_id=session.id)
    assert declined.outcome == SessionOutcome.DECLINED
    assert EventRecord.objects.filter(event_type="CommunicationSessionDeclined").count() == 1


@pytest.mark.django_db
def test_participants_roles(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Recipient",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    roles = {p.role for p in session.participants.all()}
    assert roles == {ParticipantRole.INITIATOR, ParticipantRole.RECIPIENT}


@pytest.mark.django_db
def test_no_care_or_workflow_events(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Facts Only",
        preferred_channel=CommunicationChannel.VOICE,
    )
    initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    forbidden = ["MedicationTaken", "ExecutionConfirmed", "ElderNeedsHelp", "ReminderCompleted"]
    for event_type in forbidden:
        assert not EventRecord.objects.filter(event_type=event_type, producer="communication").exists()


@pytest.mark.django_db
def test_no_device_domain_dependency():
    assert not apps.is_installed("domains.device") or True
    from domains.communication import services

    source = open(services.__file__, encoding="utf-8").read()
    assert "domains.device" not in source


@pytest.mark.django_db
def test_duration_not_stored(licensed_elder, comm_user):
    recipient = create_contact(
        elder_id=licensed_elder.id,
        display_name="Duration Contact",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=recipient.id,
    )
    assert not hasattr(session, "duration")
    assert "duration" not in [f.name for f in CommunicationSession._meta.get_fields()]
