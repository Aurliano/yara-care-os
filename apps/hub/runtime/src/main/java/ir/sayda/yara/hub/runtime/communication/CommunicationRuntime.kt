package ir.sayda.yara.hub.runtime.communication

import ir.sayda.yara.hub.core.communication.ActiveCallExistsException
import ir.sayda.yara.hub.core.communication.CallDirection
import ir.sayda.yara.hub.core.communication.CallMediaEngine
import ir.sayda.yara.hub.core.communication.CallMediaEvent
import ir.sayda.yara.hub.core.communication.CommunicationGateway
import ir.sayda.yara.hub.core.communication.CommunicationRepository
import ir.sayda.yara.hub.core.di.ApplicationScope
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.CommunicationSession
import ir.sayda.yara.hub.core.domain.model.isActive
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CommunicationRuntime(
    private val gateway: CommunicationGateway,
    private val repository: CommunicationRepository,
    private val presentationGateway: CommunicationPresentationGateway,
    private val callEngine: CallMediaEngine,
    private val nowMillis: () -> Long,
    private val scope: CoroutineScope,
    private val replicaRepository: CommunicationReplicaRepository? = null,
    private val connectivityRepository: ConnectivityRepository? = null,
) {
    @Inject
    constructor(
        gateway: CommunicationGateway,
        repository: CommunicationRepository,
        presentationGateway: CommunicationPresentationGateway,
        callEngine: CallMediaEngine,
        @ApplicationScope scope: CoroutineScope,
        replicaRepository: CommunicationReplicaRepository,
        connectivityRepository: ConnectivityRepository,
    ) : this(
        gateway,
        repository,
        presentationGateway,
        callEngine,
        { System.currentTimeMillis() },
        scope,
        replicaRepository,
        connectivityRepository,
    )

    private val mutex = Mutex()
    private val collectorsLock = Mutex()
    private var collectorsStarted = false

    fun observeCurrent(): Flow<CallSession?> = repository.observeCurrent()

    suspend fun startCollectors() {
        collectorsLock.withLock {
            if (collectorsStarted) return
            collectorsStarted = true
            scope.launch {
                callEngine.observeEvents().collect { event -> handleMediaEvent(event) }
            }
            scope.launch {
                replicaRepository?.observeSessions()?.collect { sessions ->
                    maybeAcceptIncoming(sessions)
                }
            }
            scope.launch {
                connectivityRepository?.observeOnline()
                    ?.distinctUntilChanged()
                    ?.drop(1)
                    ?.collect { online ->
                        if (online) {
                            reconnect()
                        } else {
                            handleNetworkLost()
                        }
                    }
            }
        }
    }

    suspend fun startCall(
        elderId: String,
        channel: String,
        recipientContactId: String,
    ): AppResult<CallSession> {
        startCollectors()
        val prepared = mutex.withLock {
            val current = repository.getCurrent()
            if (current != null && current.runtimeState.isActive() && current.expiresAtEpochMillis > nowMillis()) {
                return@withLock AppResult.Success(current)
            }
            when (val started = gateway.startCall(elderId, channel, recipientContactId)) {
                is AppResult.Success -> persistConnecting(
                    started.data.copy(direction = CallDirection.Outgoing),
                )
                is AppResult.Error -> {
                    if (started.exception is ActiveCallExistsException) {
                        prepareIncoming(elderId, channel, recipientContactId)
                    } else {
                        started
                    }
                }
            }
        }
        return joinPrepared(prepared)
    }

    suspend fun joinIncomingCall(
        elderId: String,
        channel: String = "VOICE",
        recipientContactId: String = "",
    ): AppResult<CallSession> {
        startCollectors()
        val prepared = mutex.withLock {
            val current = repository.getCurrent()
            if (current != null && current.runtimeState.isActive() && current.expiresAtEpochMillis > nowMillis()) {
                return@withLock AppResult.Success(current)
            }
            prepareIncoming(elderId, channel, recipientContactId)
        }
        return joinPrepared(prepared)
    }

    suspend fun reconnect(): AppResult<CallSession?> {
        startCollectors()
        val prepared = mutex.withLock {
            val current = repository.getCurrent() ?: return@withLock null
            if (!current.runtimeState.isActive()) return@withLock null
            val refreshed = if (current.expiresAtEpochMillis <= nowMillis()) {
                when (val token = gateway.refreshJoinToken(current.elderId)) {
                    is AppResult.Error -> return AppResult.Error(token.exception, token.message)
                    is AppResult.Success -> current.copy(
                        sessionId = token.data.sessionId.ifBlank { current.sessionId },
                        joinToken = token.data.joinToken,
                        expiresAtEpochMillis = token.data.expiresAtEpochMillis,
                    )
                }
            } else {
                current
            }
            persistAndPresent(
                refreshed.copy(
                    runtimeState = CallRuntimeState.Reconnecting,
                    updatedAtEpochMillis = nowMillis(),
                ),
            )
        } ?: return AppResult.Success(null)
        return when (val joined = joinPrepared(prepared)) {
            is AppResult.Error -> joined
            is AppResult.Success -> AppResult.Success(joined.data)
        }
    }

    suspend fun endCall(): AppResult<Unit> {
        val current = mutex.withLock { repository.getCurrent() } ?: return AppResult.Success(Unit)
        callEngine.leave()
        return mutex.withLock {
            when (val ended = gateway.endCall(current.sessionId)) {
                is AppResult.Error -> ended
                is AppResult.Success -> {
                    persistAndPresent(
                        current.copy(
                            runtimeState = CallRuntimeState.Finished,
                            updatedAtEpochMillis = nowMillis(),
                        ),
                    )
                    repository.clear()
                    AppResult.Success(Unit)
                }
            }
        }
    }

    suspend fun markConnected(): AppResult<CallSession> = mutex.withLock {
        val current = repository.getCurrent()
            ?: return@withLock AppResult.Error(IllegalStateException("No current call session."))
        if (current.runtimeState == CallRuntimeState.Connected) {
            return@withLock AppResult.Success(current)
        }
        if (
            current.runtimeState != CallRuntimeState.Connecting &&
            current.runtimeState != CallRuntimeState.Reconnecting
        ) {
            return@withLock AppResult.Error(IllegalStateException("Call is not connecting."))
        }
        persistAndPresent(
            current.copy(
                runtimeState = CallRuntimeState.Connected,
                updatedAtEpochMillis = nowMillis(),
            ),
        )
    }

    suspend fun mute() = callEngine.mute()
    suspend fun unmute() = callEngine.unmute()
    suspend fun cameraOn() = callEngine.cameraOn()
    suspend fun cameraOff() = callEngine.cameraOff()
    suspend fun speaker() = callEngine.speaker()

    suspend fun recover(): AppResult<CallSession?> {
        startCollectors()
        val current = mutex.withLock {
            val stored = repository.getCurrent() ?: return@withLock null
            if (!stored.runtimeState.isActive()) {
                repository.clear()
                return@withLock null
            }
            if (stored.expiresAtEpochMillis <= nowMillis()) {
                gateway.endCall(stored.sessionId)
                repository.clear()
                return@withLock null
            }
            presentationGateway.onCallSession(stored)
            stored
        } ?: return AppResult.Success(null)
        joinMedia(current.joinToken)
        markConnectedAfterJoin()
        return AppResult.Success(repository.getCurrent() ?: current)
    }

    private suspend fun prepareIncoming(
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
                persistConnecting(
                    refreshed.data.copy(
                        sessionId = sessionId,
                        elderId = elderId,
                        channel = channel.ifBlank { refreshed.data.channel.ifBlank { "VOICE" } },
                        recipientContactId = recipientContactId.ifBlank { refreshed.data.recipientContactId },
                        direction = CallDirection.Incoming,
                    ),
                )
            }
        }
    }

    private suspend fun persistConnecting(session: CallSession): AppResult<CallSession> =
        persistAndPresent(
            session.copy(
                runtimeState = CallRuntimeState.Connecting,
                updatedAtEpochMillis = nowMillis(),
            ),
        )

    private suspend fun joinPrepared(prepared: AppResult<CallSession>): AppResult<CallSession> {
        val session = when (prepared) {
            is AppResult.Error -> return prepared
            is AppResult.Success -> prepared.data
        }
        if (session.runtimeState == CallRuntimeState.Connected) {
            return prepared
        }
        joinMedia(session.joinToken)
        return markConnectedAfterJoin()
    }

    private suspend fun joinMedia(loginUrl: String) {
        if (loginUrl.isBlank()) return
        callEngine.join(loginUrl)
    }

    private suspend fun markConnectedAfterJoin(): AppResult<CallSession> = mutex.withLock {
        val current = repository.getCurrent()
            ?: return@withLock AppResult.Error(IllegalStateException("No current call session."))
        if (
            current.runtimeState == CallRuntimeState.Connecting ||
            current.runtimeState == CallRuntimeState.Reconnecting ||
            current.runtimeState == CallRuntimeState.ConnectionLost
        ) {
            persistAndPresent(
                current.copy(
                    runtimeState = CallRuntimeState.Connected,
                    updatedAtEpochMillis = nowMillis(),
                ),
            )
        } else {
            AppResult.Success(current)
        }
    }

    private suspend fun handleMediaEvent(event: CallMediaEvent) {
        mutex.withLock {
            val current = repository.getCurrent() ?: return@withLock
            when (event) {
                CallMediaEvent.Joined, CallMediaEvent.ConnectionRestored -> {
                    if (current.runtimeState.isActive() && current.runtimeState != CallRuntimeState.Connected) {
                        persistAndPresent(
                            current.copy(
                                runtimeState = CallRuntimeState.Connected,
                                updatedAtEpochMillis = nowMillis(),
                            ),
                        )
                    }
                }
                CallMediaEvent.ConnectionLost -> {
                    if (
                        current.runtimeState == CallRuntimeState.Connected ||
                        current.runtimeState == CallRuntimeState.Connecting ||
                        current.runtimeState == CallRuntimeState.Reconnecting
                    ) {
                        persistAndPresent(
                            current.copy(
                                runtimeState = CallRuntimeState.ConnectionLost,
                                updatedAtEpochMillis = nowMillis(),
                            ),
                        )
                    }
                }
                CallMediaEvent.Left -> Unit
            }
        }
    }

    private suspend fun handleNetworkLost() {
        mutex.withLock {
            val current = repository.getCurrent() ?: return@withLock
            if (current.runtimeState == CallRuntimeState.Connected) {
                persistAndPresent(
                    current.copy(
                        runtimeState = CallRuntimeState.ConnectionLost,
                        updatedAtEpochMillis = nowMillis(),
                    ),
                )
            }
        }
    }

    private suspend fun maybeAcceptIncoming(sessions: List<CommunicationSession>) {
        val ringing = sessions.firstOrNull { session ->
            session.channel != "MESSAGE" && session.status in INCOMING_STATUSES
        } ?: return
        val local = repository.getCurrent()
        if (local != null && local.runtimeState.isActive()) return
        joinIncomingCall(
            elderId = ringing.elderId,
            channel = ringing.channel.ifBlank { "VOICE" },
        )
    }

    private suspend fun persistAndPresent(session: CallSession): AppResult<CallSession> {
        repository.saveCurrent(session)
        presentationGateway.onCallSession(session)
        return AppResult.Success(session)
    }

    private companion object {
        val INCOMING_STATUSES = setOf("INITIATED", "CONNECTING", "CONNECTED")
    }
}
