package ir.sayda.yara.hub.runtime.communication

import ir.sayda.yara.hub.core.communication.ActiveCallExistsException
import ir.sayda.yara.hub.core.communication.CommunicationGateway
import ir.sayda.yara.hub.core.communication.CommunicationRepository
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CommunicationRuntimeTest {

    @Test
    fun startCallPersistsConnectingSessionAndNotifiesUi() = runTest {
        val gateway = FakeGateway()
        val repository = InMemoryCommunicationRepository()
        val presentation = RecordingPresentationGateway()
        val runtime = CommunicationRuntime(gateway, repository, presentation) { NOW }

        val result = runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        assertTrue(result is AppResult.Success)
        val session = (result as AppResult.Success).data
        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connecting, session.runtimeState)
        assertEquals("opaque-join-token", session.joinToken)
        assertEquals(session, repository.getCurrent())
        assertEquals(session, presentation.lastSession)
        assertEquals(1, gateway.startCount)
    }

    @Test
    fun secondStartCallReusesLocalActiveSession() = runTest {
        val gateway = FakeGateway()
        val runtime = CommunicationRuntime(
            gateway,
            InMemoryCommunicationRepository(),
            RecordingPresentationGateway(),
        ) { NOW }

        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)
        val second = runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        assertTrue(second is AppResult.Success)
        assertEquals(1, gateway.startCount)
        assertEquals("session-1", (second as AppResult.Success).data.sessionId)
    }

    @Test
    fun backendConflictJoinsExistingSessionViaRefresh() = runTest {
        val gateway = FakeGateway(startError = ActiveCallExistsException())
        val repository = InMemoryCommunicationRepository()
        val runtime = CommunicationRuntime(
            gateway,
            repository,
            RecordingPresentationGateway(),
        ) { NOW }

        val result = runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        assertTrue(result is AppResult.Success)
        val session = (result as AppResult.Success).data
        assertEquals("existing-session", session.sessionId)
        assertEquals("refreshed-token", session.joinToken)
        assertEquals(1, gateway.refreshCount)
        assertEquals(session, repository.getCurrent())
    }

    @Test
    fun markConnectedMovesConnectingToConnected() = runTest {
        val repository = InMemoryCommunicationRepository()
        val runtime = CommunicationRuntime(
            FakeGateway(),
            repository,
            RecordingPresentationGateway(),
        ) { NOW }
        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        val connected = runtime.markConnected()

        assertTrue(connected is AppResult.Success)
        assertEquals(CallRuntimeState.Connected, (connected as AppResult.Success).data.runtimeState)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)
    }

    @Test
    fun endCallFinishesAndClearsLocalSession() = runTest {
        val gateway = FakeGateway()
        val repository = InMemoryCommunicationRepository()
        val runtime = CommunicationRuntime(gateway, repository, RecordingPresentationGateway()) { NOW }
        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        val ended = runtime.endCall()

        assertTrue(ended is AppResult.Success)
        assertEquals(listOf("session-1"), gateway.endedSessionIds)
        assertNull(repository.getCurrent())
    }

    @Test
    fun recoverRestoresUnexpiredConnectingSession() = runTest {
        val repository = InMemoryCommunicationRepository()
        val presentation = RecordingPresentationGateway()
        repository.saveCurrent(sampleSession(expiresAt = NOW + 60_000L))
        val runtime = CommunicationRuntime(
            FakeGateway(),
            repository,
            presentation,
        ) { NOW }

        val recovered = runtime.recover()

        assertTrue(recovered is AppResult.Success)
        assertEquals("session-1", (recovered as AppResult.Success).data?.sessionId)
        assertEquals("session-1", presentation.lastSession?.sessionId)
    }

    @Test
    fun recoverEndsExpiredSessionAndReturnsIdle() = runTest {
        val gateway = FakeGateway()
        val repository = InMemoryCommunicationRepository()
        repository.saveCurrent(sampleSession(expiresAt = NOW - 1L))
        val runtime = CommunicationRuntime(gateway, repository, RecordingPresentationGateway()) { NOW }

        val recovered = runtime.recover()

        assertTrue(recovered is AppResult.Success)
        assertNull((recovered as AppResult.Success).data)
        assertNull(repository.getCurrent())
        assertEquals(listOf("session-1"), gateway.endedSessionIds)
    }

    private class FakeGateway(
        private val startError: Throwable? = null,
    ) : CommunicationGateway {
        var startCount = 0
        var refreshCount = 0
        val endedSessionIds = mutableListOf<String>()

        override suspend fun startCall(
            elderId: String,
            channel: String,
            recipientContactId: String,
        ): AppResult<CallSession> {
            startCount += 1
            if (startError != null) return AppResult.Error(startError)
            return AppResult.Success(sampleSession())
        }

        override suspend fun endCall(sessionId: String): AppResult<Unit> {
            endedSessionIds += sessionId
            return AppResult.Success(Unit)
        }

        override suspend fun refreshJoinToken(elderId: String): AppResult<CallSession> {
            refreshCount += 1
            return AppResult.Success(
                sampleSession().copy(
                    sessionId = "existing-session",
                    joinToken = "refreshed-token",
                ),
            )
        }
    }

    private class InMemoryCommunicationRepository : CommunicationRepository {
        private val current = MutableStateFlow<CallSession?>(null)

        override suspend fun saveCurrent(session: CallSession) {
            current.value = session
        }

        override suspend fun getCurrent(): CallSession? = current.value

        override suspend fun clear() {
            current.value = null
        }

        override fun observeCurrent(): Flow<CallSession?> = current
    }

    private class RecordingPresentationGateway : CommunicationPresentationGateway {
        var lastSession: CallSession? = null
        override suspend fun onCallSession(session: CallSession) {
            lastSession = session
        }
        override fun observeCallSessions(): Flow<CallSession> = MutableStateFlow(
            lastSession ?: sampleSession(),
        )
    }

    private companion object {
        const val NOW = 1_700_000_000_000L
        const val ELDER_ID = "elder-1"
        const val CONTACT_ID = "contact-1"

        fun sampleSession(expiresAt: Long = NOW + 3_600_000L) = CallSession(
            sessionId = "session-1",
            elderId = ELDER_ID,
            channel = "VOICE",
            recipientContactId = CONTACT_ID,
            runtimeState = CallRuntimeState.Connecting,
            joinToken = "opaque-join-token",
            expiresAtEpochMillis = expiresAt,
            updatedAtEpochMillis = NOW,
        )
    }
}
