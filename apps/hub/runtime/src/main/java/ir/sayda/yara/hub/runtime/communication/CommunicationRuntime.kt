package ir.sayda.yara.hub.runtime.communication

import ir.sayda.yara.hub.core.communication.ActiveCallExistsException
import ir.sayda.yara.hub.core.communication.CommunicationGateway
import ir.sayda.yara.hub.core.communication.CommunicationRepository
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.isActive
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CommunicationRuntime(
    private val gateway: CommunicationGateway,
    private val repository: CommunicationRepository,
    private val presentationGateway: CommunicationPresentationGateway,
    private val nowMillis: () -> Long,
) {
    @Inject
    constructor(
        gateway: CommunicationGateway,
        repository: CommunicationRepository,
        presentationGateway: CommunicationPresentationGateway,
    ) : this(
        gateway,
        repository,
        presentationGateway,
        { System.currentTimeMillis() },
    )

    private val mutex = Mutex()

    fun observeCurrent(): Flow<CallSession?> = repository.observeCurrent()

    suspend fun startCall(
        elderId: String,
        channel: String,
        recipientContactId: String,
    ): AppResult<CallSession> = mutex.withLock {
        val current = repository.getCurrent()
        if (current != null && current.runtimeState.isActive() && current.expiresAtEpochMillis > nowMillis()) {
            return@withLock AppResult.Success(current)
        }

        when (val started = gateway.startCall(elderId, channel, recipientContactId)) {
            is AppResult.Success -> persistAndPresent(started.data)
            is AppResult.Error -> {
                if (started.exception is ActiveCallExistsException) {
                    joinExistingSession(elderId, channel, recipientContactId)
                } else {
                    started
                }
            }
        }
    }

    suspend fun endCall(): AppResult<Unit> = mutex.withLock {
        val current = repository.getCurrent() ?: return@withLock AppResult.Success(Unit)
        when (val ended = gateway.endCall(current.sessionId)) {
            is AppResult.Error -> ended
            is AppResult.Success -> {
                val finished = current.copy(
                    runtimeState = CallRuntimeState.Finished,
                    updatedAtEpochMillis = nowMillis(),
                )
                persistAndPresent(finished)
                repository.clear()
                AppResult.Success(Unit)
            }
        }
    }

    suspend fun markConnected(): AppResult<CallSession> = mutex.withLock {
        val current = repository.getCurrent()
            ?: return@withLock AppResult.Error(IllegalStateException("No current call session."))
        if (current.runtimeState == CallRuntimeState.Connected) {
            return@withLock AppResult.Success(current)
        }
        if (current.runtimeState != CallRuntimeState.Connecting) {
            return@withLock AppResult.Error(IllegalStateException("Call is not connecting."))
        }
        persistAndPresent(
            current.copy(
                runtimeState = CallRuntimeState.Connected,
                updatedAtEpochMillis = nowMillis(),
            ),
        )
    }

    suspend fun recover(): AppResult<CallSession?> = mutex.withLock {
        val current = repository.getCurrent() ?: return@withLock AppResult.Success(null)
        if (!current.runtimeState.isActive()) {
            repository.clear()
            return@withLock AppResult.Success(null)
        }
        if (current.expiresAtEpochMillis <= nowMillis()) {
            gateway.endCall(current.sessionId)
            repository.clear()
            return@withLock AppResult.Success(null)
        }
        presentationGateway.onCallSession(current)
        AppResult.Success(current)
    }

    private suspend fun joinExistingSession(
        elderId: String,
        channel: String,
        recipientContactId: String,
    ): AppResult<CallSession> {
        return when (val refreshed = gateway.refreshJoinToken(elderId)) {
            is AppResult.Error -> refreshed
            is AppResult.Success -> {
                val sessionId = refreshed.data.sessionId
                if (sessionId.isBlank()) {
                    return AppResult.Error(ActiveCallExistsException())
                }
                persistAndPresent(
                    refreshed.data.copy(
                        sessionId = sessionId,
                        elderId = elderId,
                        channel = channel.ifBlank { refreshed.data.channel },
                        recipientContactId = recipientContactId.ifBlank { refreshed.data.recipientContactId },
                        runtimeState = CallRuntimeState.Connecting,
                        updatedAtEpochMillis = nowMillis(),
                    ),
                )
            }
        }
    }

    private suspend fun persistAndPresent(session: CallSession): AppResult<CallSession> {
        repository.saveCurrent(session)
        presentationGateway.onCallSession(session)
        return AppResult.Success(session)
    }
}
