package ir.sayda.yara.hub.runtime.communication

import ir.sayda.yara.hub.core.communication.ActiveCallExistsException
import ir.sayda.yara.hub.core.communication.CallDirection
import ir.sayda.yara.hub.core.communication.CallMediaEvent
import ir.sayda.yara.hub.core.communication.CommunicationGateway
import ir.sayda.yara.hub.core.communication.CommunicationRepository
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.CommunicationSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.model.ConnectivitySnapshot
import ir.sayda.yara.hub.core.domain.model.ConnectivityState
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CommunicationRuntimeTest {

    @Test
    fun outgoingStartCallJoinsEngineWithBackendLoginUrl() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val repository = InMemoryCommunicationRepository()
        val runtime = runtime(gateway, repository, client, this)

        val result = runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        assertTrue(result is AppResult.Success)
        val session = (result as AppResult.Success).data
        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connected, session.runtimeState)
        assertEquals(CallDirection.Outgoing, session.direction)
        assertEquals(listOf("opaque-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)
    }

    @Test
    fun secondStartCallReusesLocalActiveSession() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val runtime = runtime(gateway, InMemoryCommunicationRepository(), client, this)

        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)
        val second = runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        assertTrue(second is AppResult.Success)
        assertEquals(1, gateway.startCount)
        assertEquals(1, client.joinedUrls.size)
        assertEquals("session-1", (second as AppResult.Success).data.sessionId)
    }

    @Test
    fun backendConflictJoinsIncomingSession() = runTest {
        val gateway = FakeGateway(startError = ActiveCallExistsException())
        val client = FakeSkyroomClient()
        val repository = InMemoryCommunicationRepository()
        val runtime = runtime(gateway, repository, client, this)

        val result = runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        assertTrue(result is AppResult.Success)
        val session = (result as AppResult.Success).data
        assertEquals("existing-session", session.sessionId)
        assertEquals("refreshed-token", session.joinToken)
        assertEquals(CallDirection.Incoming, session.direction)
        assertEquals(CallRuntimeState.Connected, session.runtimeState)
        assertEquals(listOf("refreshed-token"), client.joinedUrls)
    }

    @Test
    fun joinIncomingCallUsesRefreshTokenAsLoginUrl() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val runtime = runtime(gateway, InMemoryCommunicationRepository(), client, this)

        val result = runtime.joinIncomingCall(ELDER_ID, "VIDEO")

        assertTrue(result is AppResult.Success)
        assertEquals(CallDirection.Incoming, (result as AppResult.Success).data.direction)
        assertEquals(listOf("refreshed-token"), client.joinedUrls)
        assertEquals(1, gateway.refreshCount)
        assertEquals(0, gateway.startCount)
    }

    @Test
    fun replicaIncomingSessionStartsJoin() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val replica = InMemoryReplicaRepository()
        val runtime = runtime(
            gateway,
            InMemoryCommunicationRepository(),
            client,
            this,
            replica = replica,
        )
        runtime.startCollectors()
        replica.emit(
            CommunicationSession(
                id = "replica-session",
                elderId = ELDER_ID,
                channel = "VOICE",
                status = "CONNECTING",
                outcome = "",
                initiatedAtEpochMillis = NOW,
                connectedAtEpochMillis = null,
                endedAtEpochMillis = null,
                externalExecutionReference = null,
                aggregateVersion = 1,
                updatedAtEpochMillis = NOW,
            ),
        )
        advanceUntilIdle()

        assertEquals(listOf("refreshed-token"), client.joinedUrls)
        assertEquals(1, gateway.refreshCount)
    }

    @Test
    fun connectionLostKeepsSessionAndReconnectJoinsAgain() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val repository = InMemoryCommunicationRepository()
        val runtime = runtime(gateway, repository, client, this)
        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        client.emit(CallMediaEvent.ConnectionLost)
        advanceUntilIdle()
        assertEquals(CallRuntimeState.ConnectionLost, repository.getCurrent()?.runtimeState)

        val reconnected = runtime.reconnect()
        assertTrue(reconnected is AppResult.Success)
        assertEquals(2, client.joinedUrls.size)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)
    }

    @Test
    fun connectionRestoredMarksConnected() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val repository = InMemoryCommunicationRepository()
        val runtime = runtime(gateway, repository, client, this)
        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)
        client.emit(CallMediaEvent.ConnectionLost)
        advanceUntilIdle()

        client.emit(CallMediaEvent.ConnectionRestored)
        advanceUntilIdle()

        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)
    }

    @Test
    fun networkDropMarksConnectionLostAndRestoreReconnects() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val repository = InMemoryCommunicationRepository()
        val connectivity = FakeConnectivity()
        val runtime = runtime(gateway, repository, client, this, connectivity = connectivity)
        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        connectivity.online.value = false
        advanceUntilIdle()
        assertEquals(CallRuntimeState.ConnectionLost, repository.getCurrent()?.runtimeState)

        connectivity.online.value = true
        advanceUntilIdle()
        assertEquals(2, client.joinedUrls.size)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)
    }

    @Test
    fun endCallLeavesEngineAndClearsLocalSession() = runTest {
        val gateway = FakeGateway()
        val client = FakeSkyroomClient()
        val repository = InMemoryCommunicationRepository()
        val runtime = runtime(gateway, repository, client, this)
        runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID)

        val ended = runtime.endCall()

        assertTrue(ended is AppResult.Success)
        assertTrue(client.commands.contains("leave"))
        assertEquals(listOf("session-1"), gateway.endedSessionIds)
        assertNull(repository.getCurrent())
    }

    @Test
    fun recoverRestoresUnexpiredSessionAndRejoins() = runTest {
        val client = FakeSkyroomClient()
        val repository = InMemoryCommunicationRepository()
        repository.saveCurrent(sampleSession(expiresAt = NOW + 60_000L))
        val runtime = runtime(FakeGateway(), repository, client, this)

        val recovered = runtime.recover()

        assertTrue(recovered is AppResult.Success)
        assertEquals("session-1", (recovered as AppResult.Success).data?.sessionId)
        assertEquals(listOf("opaque-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)
    }

    @Test
    fun recoverEndsExpiredSessionAndReturnsIdle() = runTest {
        val gateway = FakeGateway()
        val repository = InMemoryCommunicationRepository()
        repository.saveCurrent(sampleSession(expiresAt = NOW - 1L))
        val runtime = runtime(gateway, repository, FakeSkyroomClient(), this)

        val recovered = runtime.recover()

        assertTrue(recovered is AppResult.Success)
        assertNull((recovered as AppResult.Success).data)
        assertNull(repository.getCurrent())
        assertEquals(listOf("session-1"), gateway.endedSessionIds)
    }

    @Test
    fun mediaControlsPassThroughEngine() = runTest {
        val client = FakeSkyroomClient()
        val runtime = runtime(FakeGateway(), InMemoryCommunicationRepository(), client, this)

        runtime.mute()
        runtime.unmute()
        runtime.cameraOn()
        runtime.cameraOff()
        runtime.speaker()

        assertEquals(listOf("mute", "unmute", "cameraOn", "cameraOff", "speaker"), client.commands)
    }

    private fun runtime(
        gateway: CommunicationGateway,
        repository: CommunicationRepository,
        client: FakeSkyroomClient,
        scope: CoroutineScope,
        replica: CommunicationReplicaRepository? = null,
        connectivity: ConnectivityRepository? = null,
        presentation: RecordingPresentationGateway = RecordingPresentationGateway(),
    ) = CommunicationRuntime(
        gateway,
        repository,
        presentation,
        SkyroomCallEngine(client),
        { NOW },
        scope,
        replica,
        connectivity,
    )

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

    private class InMemoryReplicaRepository : CommunicationReplicaRepository {
        private val sessions = MutableStateFlow<List<CommunicationSession>>(emptyList())
        override fun observePriorityContacts(elderId: String): Flow<List<Contact>> =
            MutableStateFlow(emptyList())
        override fun observeSessions(): Flow<List<CommunicationSession>> = sessions
        override suspend fun upsertContact(contact: Contact) = Unit
        override suspend fun upsertSession(session: CommunicationSession) = Unit
        fun emit(session: CommunicationSession) {
            sessions.value = listOf(session)
        }
    }

    private class FakeConnectivity : ConnectivityRepository {
        val online = MutableStateFlow(true)
        override fun observeOnline(): Flow<Boolean> = online
        override suspend fun isOnline(): Boolean = online.value
        override fun observeConnectivity(): Flow<ConnectivitySnapshot> =
            MutableStateFlow(
                ConnectivitySnapshot(
                    state = ConnectivityState.CONNECTED,
                    isBackendReachable = true,
                ),
            )
        override suspend fun refreshBackendReachability(): ConnectivitySnapshot =
            ConnectivitySnapshot(
                state = ConnectivityState.CONNECTED,
                isBackendReachable = true,
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
