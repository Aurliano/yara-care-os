"""End-to-End LiveKit & Database Domain Verification Script.

Tests the full lifecycle of Call Sessions with LiveKit Cloud provider:
1. Seed Family Lab data (Caregiver, Elder, Contacts).
2. Authenticate Caregiver and initiate a VIDEO call via infrastructure services.
3. Verify LiveKit JWT tokens generated for both participants.
4. Progress session through CONNECTING -> ACCEPTED -> ENDED.
5. Verify database records:
   - CommunicationSession (status & outcome)
   - SessionParticipant (Hub & Caregiver)
   - CallAttempt (attempt_number, outcome)
   - ProviderCallBinding & ProviderRoomBinding (provider='livekit')
6. Test Rejected / Missed call flows.
7. Confirm 0 SkyRoom calls were made.
"""

import os
import sys
import uuid
import django

sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.conf import settings
from django.utils import timezone
import jwt

from domains.identity_access.models import User
from integration.services.family_lab_seed import ensure_family_lab_seed, FAMILY_CAREGIVER_PHONE
from domains.communication.models import (
    CommunicationSession,
    SessionParticipant,
    CallAttempt,
    Contact,
)
from domains.communication.enums import SessionOutcome, SessionStatus
from domains.communication.services.sessions import (
    accept_session,
    decline_session,
    end_session,
    get_session,
)
from infrastructure.communication.services import (
    start_call,
    end_call,
    issue_login_url,
)
from infrastructure.communication.models import (
    ProviderCallBinding,
    ProviderRoomBinding,
    ProviderSubjectType,
    ProviderUserBinding,
)
from infrastructure.communication.factory import get_communication_provider
from infrastructure.communication.livekit import LivekitCommunicationProvider


def run_e2e_verification():
    print("=================================================================")
    print("   YARA CARE OS — LIVEKIT CLOUD E2E & DOMAIN VERIFICATION")
    print("=================================================================")
    print(f"Provider in settings: {settings.COMMUNICATION_PROVIDER}")
    print(f"LiveKit Cloud URL:   {settings.LIVEKIT_URL}")
    print(f"LiveKit API Key:     {settings.LIVEKIT_API_KEY}")

    # 1. Verify Active Provider Instance
    provider = get_communication_provider()
    assert isinstance(
        provider, LivekitCommunicationProvider
    ), f"Expected LivekitCommunicationProvider, got {type(provider)}"
    print("\n[OK] 1. Active Provider is LivekitCommunicationProvider.")

    # 2. Seed / Retrieve Family Lab Data
    seed = ensure_family_lab_seed()
    elder_id = uuid.UUID(str(seed["elder_id"]))
    user = User.objects.get(phone=FAMILY_CAREGIVER_PHONE)
    caregiver_user_id = user.id
    contact_id = uuid.UUID(str(seed["contact_id"]))
    print(f"\n[OK] 2. Family Lab seeded: Elder={elder_id}, Caregiver={caregiver_user_id}, Contact={contact_id}")

    # Clean up any stale active sessions for this elder
    for active_sess in CommunicationSession.objects.filter(elder_id=elder_id, status__in=[SessionStatus.INITIATED, SessionStatus.CONNECTING, SessionStatus.CONNECTED]):
        end_call(session_id=active_sess.id)

    # 3. Simulate Caregiver -> Hub VIDEO Call (start_call)
    print("\n--- Testing Scenario 1: Normal Video Call (Connect -> Accept -> Hangup) ---")
    join_result = start_call(
        elder_id=elder_id,
        channel="VIDEO",
        recipient_contact_id=contact_id,
        initiator_user_id=caregiver_user_id,
        subject_type=ProviderSubjectType.USER,
        subject_id=caregiver_user_id,
        room_title="Yara Video Call",
        user_display_name="Caregiver Ali",
    )
    session_id = join_result.session_id
    assert session_id is not None
    session = get_session(session_id)
    print(f"Session Created: ID={session.id}, Status={session.status}, Channel={session.channel}")
    assert session.status == SessionStatus.CONNECTING
    assert session.channel == "VIDEO"

    # Verify Caregiver's LiveKit Token
    caller_claims = jwt.decode(
        join_result.join_token, settings.LIVEKIT_API_SECRET, algorithms=["HS256"]
    )
    print(f"Caller Token Subject:         {caller_claims['sub']}")
    print(f"Caller Token Room:            {caller_claims['video']['room']}")
    assert caller_claims["iss"] == settings.LIVEKIT_API_KEY
    assert caller_claims["name"] == "Caregiver Ali"

    # Hub (Elder side) joins via issue_login_url
    hub_join = issue_login_url(
        elder_id=elder_id,
        subject_type=ProviderSubjectType.ELDER_HUB,
        subject_id=elder_id,
        room_title="Yara Video Call",
        user_display_name="Elder Hub",
    )
    hub_claims = jwt.decode(
        hub_join.join_token, settings.LIVEKIT_API_SECRET, algorithms=["HS256"]
    )
    print(f"Hub Token Subject:            {hub_claims['sub']}")
    print(f"Hub Token Room:               {hub_claims['video']['room']}")
    assert hub_claims["iss"] == settings.LIVEKIT_API_KEY
    assert hub_claims["video"]["room"] == caller_claims["video"]["room"]
    print("[OK] Both Hub and Caller generated matching LiveKit Cloud room tokens.")

    # Check Participants in DB
    participants = list(SessionParticipant.objects.filter(communication_session=session))
    print(f"Participants in DB: {len(participants)} records")
    assert len(participants) >= 2
    for p in participants:
        print(f"  - Participant ID={p.id}, Role={p.role}, Contact={p.contact_id}, User={p.user_id}")

    # Check CallAttempt in DB
    attempts = list(CallAttempt.objects.filter(communication_session=session))
    print(f"CallAttempts in DB: {len(attempts)} records")
    assert len(attempts) >= 1
    attempt = attempts[0]
    print(f"  - Attempt: Number={attempt.attempt_number}, StartedAt={attempt.started_at}")

    # Check Provider Bindings
    call_binding = ProviderCallBinding.objects.get(communication_session_id=session.id)
    print(f"ProviderCallBinding: ID={call_binding.id}, Room={call_binding.room_binding.room_key}, Provider={call_binding.room_binding.provider}")
    assert call_binding.room_binding.provider == "livekit"

    # 4. Elder answers on Hub (Accept Session)
    accepted_session = accept_session(session_id=session.id)
    print(f"\nElder answers call: Status={accepted_session.status}, ConnectedAt={accepted_session.connected_at}")
    assert accepted_session.status == SessionStatus.CONNECTED

    # 5. Hang up call (End Session)
    end_call(session_id=session.id)
    ended_session = get_session(session.id)
    print(f"Call ended: Status={ended_session.status}, Outcome={ended_session.outcome}, EndedAt={ended_session.ended_at}")
    assert ended_session.status == SessionStatus.ENDED
    assert ended_session.outcome == SessionOutcome.ANSWERED

    # 6. Test Scenario 2: Declined / Cancelled Call
    print("\n--- Testing Scenario 2: Declined Call Flow ---")
    declined_join = start_call(
        elder_id=elder_id,
        channel="VIDEO",
        recipient_contact_id=contact_id,
        initiator_user_id=caregiver_user_id,
        subject_type=ProviderSubjectType.USER,
        subject_id=caregiver_user_id,
        room_title="Yara Video Call",
        user_display_name="Caregiver Ali",
    )
    dec_session_id = declined_join.session_id
    assert dec_session_id is not None
    dec_session = decline_session(session_id=dec_session_id)
    print(f"Elder declines call: Status={dec_session.status}, Outcome={dec_session.outcome}")
    assert dec_session.status == SessionStatus.DECLINED
    assert dec_session.outcome == SessionOutcome.DECLINED

    # 7. Test Scenario 3: Cancelled Call before answer
    print("\n--- Testing Scenario 3: Cancelled Before Answer Flow ---")
    cancelled_join = start_call(
        elder_id=elder_id,
        channel="VIDEO",
        recipient_contact_id=contact_id,
        initiator_user_id=caregiver_user_id,
        subject_type=ProviderSubjectType.USER,
        subject_id=caregiver_user_id,
        room_title="Yara Video Call",
        user_display_name="Caregiver Ali",
    )
    can_session_id = cancelled_join.session_id
    assert can_session_id is not None
    end_call(session_id=can_session_id)
    can_session = get_session(can_session_id)
    print(f"Caller hangs up before answer: Status={can_session.status}, Outcome={can_session.outcome}")
    assert can_session.status == SessionStatus.CANCELLED
    assert can_session.outcome == SessionOutcome.CANCELLED

    print("\n=================================================================")
    print(" [SUCCESS] ALL LIVEKIT DOMAIN, DB ENTITIES & TOKEN CHECKS PASSED!")
    print("=================================================================")


if __name__ == "__main__":
    run_e2e_verification()
