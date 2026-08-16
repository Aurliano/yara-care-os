package ir.sayda.yara.hub.runtime.dispatcher

import ir.sayda.yara.hub.core.communication.CommunicationGateway
import ir.sayda.yara.hub.core.communication.CommunicationRepository
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import ir.sayda.yara.hub.runtime.communication.CommunicationRuntime
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class InitiateCallActionHandlerTest {

    @Test
    fun startsCallThroughCommunicationRuntime() = runTest {
        val gateway = RecordingGateway()
        val runtime = CommunicationRuntime(
            gateway,
            InMemoryCommunicationRepository(),
            RecordingPresentationGateway(),
        ) { 1_700_000_000_000L }
        val handler = InitiateCallActionHandler(runtime, MissingAuthRepository())
        val payload = """
            {"elder_id":"elder-1","recipient_contact_id":"contact-1","channel":"VOICE"}
        """.trimIndent()

        val result = handler.handle(payload, "exec-1")

        assertTrue(result.accepted)
        assertEquals("communication_replica_runtime", result.routedTo)
        assertEquals("elder-1", gateway.lastElderId)
        assertEquals("contact-1", gateway.lastRecipientContactId)
        assertEquals("VOICE", gateway.lastChannel)
    }

    @Test
    fun usesIdentityElderWhenPayloadOmitsElderId() = runTest {
        val gateway = RecordingGateway()
        val runtime = CommunicationRuntime(
            gateway,
            InMemoryCommunicationRepository(),
            RecordingPresentationGateway(),
        ) { 1_700_000_000_000L }
        val handler = InitiateCallActionHandler(runtime, IdentityAuthRepository("elder-from-auth"))
        val payload = """{"recipient_contact_id":"contact-9"}"""

        val result = handler.handle(payload, "exec-2")

        assertTrue(result.accepted)
        assertEquals("elder-from-auth", gateway.lastElderId)
        assertEquals("VOICE", gateway.lastChannel)
    }

    @Test
    fun rejectsMissingRecipient() = runTest {
        val runtime = CommunicationRuntime(
            RecordingGateway(),
            InMemoryCommunicationRepository(),
            RecordingPresentationGateway(),
        ) { 1_700_000_000_000L }
        val handler = InitiateCallActionHandler(runtime, MissingAuthRepository())

        val result = handler.handle("""{"elder_id":"elder-1"}""", "exec-3")

        assertTrue(!result.accepted)
    }

    private class RecordingGateway : CommunicationGateway {
        var lastElderId: String? = null
        var lastChannel: String? = null
        var lastRecipientContactId: String? = null

        override suspend fun startCall(
            elderId: String,
            channel: String,
            recipientContactId: String,
        ): AppResult<CallSession> {
            lastElderId = elderId
            lastChannel = channel
            lastRecipientContactId = recipientContactId
            return AppResult.Success(
                CallSession(
                    sessionId = "session-1",
                    elderId = elderId,
                    channel = channel,
                    recipientContactId = recipientContactId,
                    runtimeState = ir.sayda.yara.hub.core.domain.model.CallRuntimeState.Connecting,
                    joinToken = "token",
                    expiresAtEpochMillis = 1_700_003_600_000L,
                    updatedAtEpochMillis = 1_700_000_000_000L,
                ),
            )
        }

        override suspend fun endCall(sessionId: String): AppResult<Unit> = AppResult.Success(Unit)

        override suspend fun refreshJoinToken(elderId: String): AppResult<CallSession> =
            AppResult.Error(IllegalStateException("unused"))
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
        override suspend fun onCallSession(session: CallSession) = Unit
        override fun observeCallSessions(): Flow<CallSession> = MutableStateFlow(
            CallSession(
                sessionId = "unused",
                elderId = "unused",
                channel = "VOICE",
                recipientContactId = "unused",
                runtimeState = ir.sayda.yara.hub.core.domain.model.CallRuntimeState.Idle,
                joinToken = "",
                expiresAtEpochMillis = 0L,
                updatedAtEpochMillis = 0L,
            ),
        )
    }

    private class MissingAuthRepository : AuthRepository by UnsupportedAuthRepository() {
        override suspend fun getIdentity(): HubIdentity? = null
    }

    private class IdentityAuthRepository(
        private val elderId: String,
    ) : AuthRepository by UnsupportedAuthRepository() {
        override suspend fun getIdentity(): HubIdentity? = HubIdentity(
            deviceId = "device-1",
            replicaId = "replica-1",
            elderId = elderId,
            accessToken = "access",
            refreshToken = "refresh",
            tokenExpiresAtEpochMillis = 0L,
            backendUrl = "http://localhost",
            provisionedAtEpochMillis = 0L,
            lastAuthenticatedAtEpochMillis = 0L,
            provisioningState = ProvisioningState.READY,
        )
    }

    private open class UnsupportedAuthRepository : AuthRepository {
        override suspend fun getIdentity(): HubIdentity? = error("unused")
        override suspend fun saveIdentity(identity: HubIdentity) = error("unused")
        override suspend fun clearIdentity() = error("unused")
        override suspend fun login(phone: String, password: String) = error("unused")
        override suspend fun logout() = error("unused")
        override suspend fun refreshTokenIfNeeded() = error("unused")
        override suspend fun refreshToken() = error("unused")
        override fun observeIdentity(): Flow<HubIdentity?> = error("unused")
    }
}
