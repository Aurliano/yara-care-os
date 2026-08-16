package ir.sayda.yara.hub.feature.communication

import ir.sayda.yara.hub.core.communication.CallDirection
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.feature.communication.presentation.CallScreenKind
import ir.sayda.yara.hub.feature.communication.presentation.CommunicationPresentationStateMapper
import ir.sayda.yara.hub.feature.communication.presentation.ConnectionBannerKind
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CommunicationPresentationStateMapperTest {

    @Test
    fun incomingConnectingShowsIncomingScreen() {
        val ui = map(session(CallRuntimeState.Connecting, CallDirection.Incoming), "مادر")
        assertEquals(CallScreenKind.Incoming, ui.kind)
        assertEquals(R.string.call_incoming_headline, ui.headlineRes)
        assertEquals(R.string.call_incoming_status, ui.statusRes)
        assertTrue(ui.showAnswer)
        assertTrue(ui.showDecline)
        assertFalse(ui.showHangup)
    }

    @Test
    fun outgoingConnectingShowsOutgoingScreen() {
        val ui = map(session(CallRuntimeState.Connecting, CallDirection.Outgoing), "پدر")
        assertEquals(CallScreenKind.Outgoing, ui.kind)
        assertEquals(R.string.call_outgoing_headline, ui.headlineRes)
        assertTrue(ui.showHangup)
        assertTrue(ui.showWaitingIndicator)
        assertFalse(ui.showAnswer)
    }

    @Test
    fun connectedShowsTalkingWithCameraVisibleButDisabledForVoice() {
        val ui = map(
            session(CallRuntimeState.Connected, CallDirection.Outgoing, channel = "VOICE"),
            "خواهر",
        )
        assertEquals(CallScreenKind.Talking, ui.kind)
        assertEquals(R.string.call_talking_headline, ui.headlineRes)
        assertTrue(ui.showMediaControls)
        assertTrue(ui.showHangup)
        assertTrue(ui.showVoicePlaceholders)
        assertFalse(ui.cameraEnabled)
    }

    @Test
    fun videoTalkingEnablesCameraControl() {
        val ui = map(
            session(CallRuntimeState.Connected, CallDirection.Incoming, channel = "VIDEO"),
            "برادر",
            cameraOn = true,
        )
        assertTrue(ui.showMediaControls)
        assertTrue(ui.cameraEnabled)
        assertTrue(ui.cameraOn)
    }

    @Test
    fun connectionLostShowsRetryBannerAndHangup() {
        val ui = map(session(CallRuntimeState.ConnectionLost, CallDirection.Outgoing), "خاله")
        assertEquals(CallScreenKind.ConnectionLost, ui.kind)
        assertEquals(R.string.call_lost_headline, ui.headlineRes)
        assertEquals(ConnectionBannerKind.Lost, ui.bannerKind)
        assertTrue(ui.showRetry)
        assertTrue(ui.showHangup)
        assertFalse(ui.showMediaControls)
    }

    @Test
    fun reconnectingShowsRetryWaitState() {
        val ui = map(session(CallRuntimeState.Reconnecting, CallDirection.Incoming), "عمو")
        assertEquals(CallScreenKind.Retry, ui.kind)
        assertEquals(R.string.call_retry_headline, ui.headlineRes)
        assertEquals(ConnectionBannerKind.Retrying, ui.bannerKind)
        assertTrue(ui.showHangup)
        assertTrue(ui.showWaitingIndicator)
        assertFalse(ui.showRetry)
    }

    @Test
    fun finishedReturnsHome() {
        val ui = map(session(CallRuntimeState.Finished, CallDirection.Outgoing), "مادر")
        assertEquals(CallScreenKind.Finished, ui.kind)
        assertEquals(R.string.call_finished_headline, ui.headlineRes)
        assertTrue(ui.showReturnHome)
        assertFalse(ui.showHangup)
    }

    @Test
    fun startFailureShowsRetryWithoutSession() {
        val ui = CommunicationPresentationStateMapper.map(
            session = null,
            contactName = "پدر",
            startFailed = true,
        )
        assertEquals(CallScreenKind.Retry, ui.kind)
        assertEquals(R.string.call_failed_headline, ui.headlineRes)
        assertEquals(R.string.call_failed_status, ui.statusRes)
        assertEquals(ConnectionBannerKind.Failed, ui.bannerKind)
        assertTrue(ui.showRetry)
        assertTrue(ui.showReturnHome)
    }

    @Test
    fun awaitingOutgoingShowsOutgoingBeforeSession() {
        val ui = CommunicationPresentationStateMapper.map(
            session = null,
            contactName = "مادر",
            awaitingOutgoing = true,
        )
        assertEquals(CallScreenKind.Outgoing, ui.kind)
        assertEquals(R.string.call_outgoing_headline, ui.headlineRes)
        assertTrue(ui.showHangup)
    }

    @Test
    fun locallyFinishedShowsFinishedWithoutSession() {
        val ui = CommunicationPresentationStateMapper.map(
            session = null,
            contactName = "مادر",
            locallyFinished = true,
        )
        assertEquals(CallScreenKind.Finished, ui.kind)
        assertTrue(ui.showReturnHome)
    }

    @Test
    fun idleOrMissingSessionIsHidden() {
        assertEquals(CallScreenKind.Hidden, CommunicationPresentationStateMapper.kindFor(null))
        assertEquals(
            CallScreenKind.Hidden,
            CommunicationPresentationStateMapper.kindFor(session(CallRuntimeState.Idle)),
        )
    }

    @Test
    fun contactNameFallsBackToEmptyForFamilyResource() {
        val active = session(CallRuntimeState.Connected, recipientContactId = "missing")
        assertEquals(
            "",
            CommunicationPresentationStateMapper.resolvedContactName(active, emptyList()),
        )
        assertEquals(
            "مادر",
            CommunicationPresentationStateMapper.resolvedContactName(
                session = active.copy(recipientContactId = "c1"),
                contacts = listOf(contact("c1", "مادر")),
            ),
        )
        assertEquals(
            "پدر",
            CommunicationPresentationStateMapper.resolvedContactName(active, emptyList(), fallbackName = "پدر"),
        )
        assertNull(map(active, "").bannerKind)
    }

    @Test
    fun mutedTalkingUsesMutedStatusResource() {
        val ui = map(
            session(CallRuntimeState.Connected, CallDirection.Outgoing),
            "مادر",
            muted = true,
        )
        assertEquals(R.string.call_talking_muted_status, ui.statusRes)
    }

    private fun map(
        session: CallSession?,
        contactName: String,
        muted: Boolean = false,
        cameraOn: Boolean = false,
    ) = CommunicationPresentationStateMapper.map(
        session = session,
        contactName = contactName,
        muted = muted,
        cameraOn = cameraOn,
    )

    private fun session(
        state: CallRuntimeState,
        direction: CallDirection = CallDirection.Outgoing,
        channel: String = "VOICE",
        recipientContactId: String = "c1",
    ) = CallSession(
        sessionId = "s1",
        elderId = "e1",
        channel = channel,
        recipientContactId = recipientContactId,
        runtimeState = state,
        joinToken = "token",
        expiresAtEpochMillis = 1L,
        updatedAtEpochMillis = 1L,
        direction = direction,
    )

    private fun contact(id: String, name: String) = Contact(
        id = id,
        elderId = "e1",
        displayName = name,
        phone = "",
        communicationIdentitiesJson = "",
        preferredChannel = "VOICE",
        photoReference = null,
        isPriority = true,
        status = "ACTIVE",
        updatedAtEpochMillis = 1L,
    )
}
