package ir.sayda.yara.hub.feature.communication

import ir.sayda.yara.hub.core.communication.CallDirection
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.Contact
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CallPresentationTest {

    @Test
    fun incomingConnectingShowsIncomingScreen() {
        val ui = toCallUiModel(session(CallRuntimeState.Connecting, CallDirection.Incoming), "مادر")
        assertEquals(CallScreenKind.Incoming, ui.kind)
        assertEquals("تماس ورودی", ui.headline)
        assertTrue(ui.showAnswer)
        assertTrue(ui.showDecline)
        assertFalse(ui.showHangup)
    }

    @Test
    fun outgoingConnectingShowsOutgoingScreen() {
        val ui = toCallUiModel(session(CallRuntimeState.Connecting, CallDirection.Outgoing), "پدر")
        assertEquals(CallScreenKind.Outgoing, ui.kind)
        assertEquals("در حال تماس", ui.headline)
        assertTrue(ui.showHangup)
        assertFalse(ui.showAnswer)
    }

    @Test
    fun connectedShowsTalkingScreenWithMediaControls() {
        val ui = toCallUiModel(
            session(CallRuntimeState.Connected, CallDirection.Outgoing, channel = "VOICE"),
            "خواهر",
        )
        assertEquals(CallScreenKind.Talking, ui.kind)
        assertEquals("در حال گفتگو", ui.headline)
        assertTrue(ui.showMediaControls)
        assertTrue(ui.showHangup)
        assertFalse(ui.showCamera)
    }

    @Test
    fun videoTalkingShowsCameraControl() {
        val ui = toCallUiModel(
            session(CallRuntimeState.Connected, CallDirection.Incoming, channel = "VIDEO"),
            "برادر",
            cameraOn = true,
        )
        assertTrue(ui.showCamera)
        assertTrue(ui.cameraOn)
    }

    @Test
    fun connectionLostShowsRetryAndHangup() {
        val ui = toCallUiModel(session(CallRuntimeState.ConnectionLost, CallDirection.Outgoing), "خاله")
        assertEquals(CallScreenKind.ConnectionLost, ui.kind)
        assertEquals("ارتباط قطع شد", ui.headline)
        assertTrue(ui.showRetry)
        assertTrue(ui.showHangup)
        assertFalse(ui.showMediaControls)
    }

    @Test
    fun reconnectingShowsRetryWaitState() {
        val ui = toCallUiModel(session(CallRuntimeState.Reconnecting, CallDirection.Incoming), "عمو")
        assertEquals(CallScreenKind.Retry, ui.kind)
        assertEquals("در حال تلاش دوباره", ui.headline)
        assertTrue(ui.showHangup)
        assertFalse(ui.showRetry)
    }

    @Test
    fun finishedReturnsHome() {
        val ui = toCallUiModel(session(CallRuntimeState.Finished, CallDirection.Outgoing), "مادر")
        assertEquals(CallScreenKind.Finished, ui.kind)
        assertEquals("تماس پایان یافت", ui.headline)
        assertTrue(ui.showReturnHome)
        assertFalse(ui.showHangup)
    }

    @Test
    fun startFailureShowsRetryWithoutSession() {
        val ui = toCallUiModel(session = null, contactName = "پدر", startFailed = true)
        assertEquals(CallScreenKind.Retry, ui.kind)
        assertEquals("تماس برقرار نشد", ui.headline)
        assertEquals(CallCopy.START_FAILED, ui.status)
        assertTrue(ui.showRetry)
        assertTrue(ui.showReturnHome)
    }

    @Test
    fun awaitingOutgoingShowsOutgoingBeforeSession() {
        val ui = toCallUiModel(session = null, contactName = "مادر", awaitingOutgoing = true)
        assertEquals(CallScreenKind.Outgoing, ui.kind)
        assertEquals("در حال تماس", ui.headline)
        assertTrue(ui.showHangup)
    }

    @Test
    fun locallyFinishedShowsFinishedWithoutSession() {
        val ui = toCallUiModel(session = null, contactName = "مادر", locallyFinished = true)
        assertEquals(CallScreenKind.Finished, ui.kind)
        assertTrue(ui.showReturnHome)
    }

    @Test
    fun idleOrMissingSessionIsHidden() {
        assertEquals(CallScreenKind.Hidden, callScreenKind(null))
        assertEquals(CallScreenKind.Hidden, callScreenKind(session(CallRuntimeState.Idle)))
    }

    @Test
    fun contactNameFallsBackToFamily() {
        val session = session(CallRuntimeState.Connected, recipientContactId = "missing")
        assertEquals(CallCopy.FAMILY, session.resolvedContactName(emptyList()))
        assertEquals(
            "مادر",
            session.copy(recipientContactId = "c1").resolvedContactName(listOf(contact("c1", "مادر"))),
        )
        assertEquals("پدر", session.resolvedContactName(emptyList(), fallbackName = "پدر"))
    }

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
