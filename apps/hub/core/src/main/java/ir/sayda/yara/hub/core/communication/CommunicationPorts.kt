package ir.sayda.yara.hub.core.communication

import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.result.AppResult
import kotlinx.coroutines.flow.Flow

/** Backend-only call transport. Never talks to a media vendor. */
interface CommunicationGateway {
    suspend fun startCall(
        elderId: String,
        channel: String,
        recipientContactId: String,
    ): AppResult<CallSession>

    suspend fun endCall(sessionId: String): AppResult<Unit>

    suspend fun refreshJoinToken(elderId: String): AppResult<CallSession>
}

/** Hub-owned current call row for reconnect after process death. */
interface CommunicationRepository {
    suspend fun saveCurrent(session: CallSession)
    suspend fun getCurrent(): CallSession?
    suspend fun clear()
    fun observeCurrent(): Flow<CallSession?>
}
