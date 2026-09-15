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
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.isActive
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
    private val authRepository: AuthRepository? = null,
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
        authRepository: AuthRepository,
    ) : this(
        gateway,
        repository,
        presentationGateway,
        callEngine,
        { System.currentTimeMillis() },
        scope,
        replicaRepository,
        connectivityRepository,
        authRepository,
    )

    private val mutex = Mutex()
    private val collectorsLock = Mutex()
    private var collectorsStarted = false
    @Volatile
    private var activeMediaSessionId: String? = null

    fun observeCurrent(): Flow<CallSession?> = repository.observeCurrent()

    suspend fun startCollectors() {
        collectorsLock.withLock {
            if (collectorsStarted) return
            collectorsStarted = true
            scope.launch {
                callEngine.observeEvents().collect { raw ->
                    val tagged = tagEventWithSession(raw, activeMediaSessionId)
                    handleMediaEvent(tagged)
                }
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
        val current = repository.getCurrent()
        if (current != null && current.runtimeState.isActive() && current.expiresAtEpochMillis > nowMillis()) {
            return AppResult.Success(current)
        }
        val prepared = mutex.withLock {
            val lockedCurrent = repository.getCurrent()
            if (lockedCurrent != null && lockedCurrent.runtimeState.isActive() && lockedCurrent.expiresAtEpochMillis > nowMillis()) {
                return@withLock AppResult.Success(lockedCurrent)
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
            if (current != null && current.runtimeState == CallRuntimeState.Connected && current.expiresAtEpochMillis > nowMillis() && current.joinToken.isNotBlank()) {
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
            val ended = gateway.endCall(current.sessionId)
            persistAndPresent(
                current.copy(
                    runtimeState = CallRuntimeState.Finished,
                    updatedAtEpochMillis = nowMillis(),
                ),
            )
            activeMediaSessionId = null
            repository.clear()
            when (ended) {
                is AppResult.Error -> ended
                is AppResult.Success -> AppResult.Success(Unit)
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
                expiresAtEpochMillis = nowMillis() + 14400_000L,
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
        return AppResult.Success(repository.getCurrent() ?: current)
    }

    private suspend fun prepareIncoming(
        elderId: String,
        channel: String,
        recipientContactId: String,
    ): AppResult<CallSession> {
        val currentLocal = repository.getCurrent()
        val localSessionId = currentLocal?.sessionId.orEmpty()
        return when (val refreshed = gateway.refreshJoinToken(elderId)) {
            is AppResult.Error -> refreshed
            is AppResult.Success -> {
                val sessionId = refreshed.data.sessionId.ifBlank { localSessionId }
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

    private suspend fun persistConnecting(session: CallSession): AppResult<CallSession> {
        activeMediaSessionId = session.sessionId
        return persistAndPresent(
            session.copy(
                runtimeState = CallRuntimeState.Connecting,
                updatedAtEpochMillis = nowMillis(),
            ),
        )
    }

    private suspend fun joinPrepared(prepared: AppResult<CallSession>): AppResult<CallSession> {
        val session = when (prepared) {
            is AppResult.Error -> return prepared
            is AppResult.Success -> prepared.data
        }
        if (session.runtimeState == CallRuntimeState.Connected) {
            return prepared
        }
        joinMedia(session.joinToken)
        return prepared
    }

    private suspend fun joinMedia(loginUrl: String) {
        if (loginUrl.isBlank()) return
        callEngine.join(loginUrl)
    }

    private suspend fun handleMediaEvent(event: CallMediaEvent) {
        mutex.withLock {
            val current = repository.getCurrent() ?: return@withLock
            val eventSessionId: String? = when (event) {
                is CallMediaEvent.Joined -> event.sessionId
                is CallMediaEvent.Left -> event.sessionId
                is CallMediaEvent.ConnectionLost -> event.sessionId
                is CallMediaEvent.ConnectionRestored -> event.sessionId
            }
            if (eventSessionId != null && eventSessionId != current.sessionId) {
                return@withLock
            }
            when (event) {
                is CallMediaEvent.Joined, is CallMediaEvent.ConnectionRestored -> {
                    if (current.runtimeState.isActive() && current.runtimeState != CallRuntimeState.Connected) {
                        persistAndPresent(
                            current.copy(
                                runtimeState = CallRuntimeState.Connected,
                                updatedAtEpochMillis = nowMillis(),
                                expiresAtEpochMillis = nowMillis() + 14400_000L,
                            ),
                        )
                    }
                }
                is CallMediaEvent.ConnectionLost -> {
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
                is CallMediaEvent.Left -> {
                    if (current.runtimeState.isActive()) {
                        callEngine.leave()
                        persistAndPresent(
                            current.copy(
                                runtimeState = CallRuntimeState.Finished,
                                updatedAtEpochMillis = nowMillis(),
                            ),
                        )
                        repository.clear()
                    }
                }
            }
        }
    }

    private suspend fun handleNetworkLost() {
        mutex.withLock {
            val current = repository.getCurrent() ?: return@withLock
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
    }

    suspend fun ringIncoming(
        sessionId: String = "",
        elderId: String,
        channel: String = "VOICE",
        recipientContactId: String = "",
    ): AppResult<CallSession> {
        startCollectors()
        return mutex.withLock {
            val current = repository.getCurrent()
            if (current != null && (sessionId.isBlank() || current.sessionId == sessionId) && current.runtimeState.isActive() && current.expiresAtEpochMillis > nowMillis() && current.joinToken.isNotBlank()) {
                return@withLock AppResult.Success(current)
            }
            if (sessionId.isNotBlank()) {
                val initial = (current ?: CallSession(
                    sessionId = sessionId,
                    elderId = elderId,
                    channel = channel.ifBlank { "VOICE" },
                    recipientContactId = recipientContactId,
                    runtimeState = CallRuntimeState.Connecting,
                    joinToken = "",
                    expiresAtEpochMillis = nowMillis() + 60_000L,
                    updatedAtEpochMillis = nowMillis(),
                    direction = CallDirection.Incoming,
                )).copy(
                    sessionId = sessionId,
                    direction = CallDirection.Incoming,
                    runtimeState = CallRuntimeState.Connecting,
                    channel = channel.ifBlank { "VOICE" },
                )
                persistAndPresent(initial)
            }
            prepareIncoming(elderId, channel, recipientContactId)
        }
    }

    private var pollerJob: Job? = null

    fun startIncomingCallPoller() {
        if (pollerJob != null) return
        pollerJob = scope.launch {
            while (isActive) {
                delay(2_500L)
                checkRemoteSessions()
            }
        }
    }

    fun stopIncomingCallPoller() {
        pollerJob?.cancel()
        pollerJob = null
    }

    suspend fun checkRemoteSessions() {
        val isOnline = connectivityRepository?.isOnline() ?: true
        if (!isOnline) return
        val elderId = authRepository?.getIdentity()?.elderId
        if (elderId.isNullOrBlank()) return
        when (val sessionsResult = gateway.fetchRecentSessions(elderId)) {
            is AppResult.Success -> {
                maybeAcceptIncoming(sessionsResult.data)
            }
            is AppResult.Error -> Unit
        }
    }

    private suspend fun maybeAcceptIncoming(sessions: List<CommunicationSession>) {
        val local = repository.getCurrent()
        if (local != null && local.runtimeState.isActive()) {
            val remoteMatch = sessions.firstOrNull { it.id == local.sessionId }
            if (remoteMatch != null && remoteMatch.status in TERMINAL_STATUSES) {
                mutex.withLock {
                    val current = repository.getCurrent()
                    if (current != null && current.sessionId == remoteMatch.id && current.runtimeState.isActive()) {
                        callEngine.leave()
                        persistAndPresent(
                            current.copy(
                                runtimeState = CallRuntimeState.Finished,
                                updatedAtEpochMillis = nowMillis(),
                            ),
                        )
                        repository.clear()
                    }
                }
                return
            }
        }

        val ringing = sessions.firstOrNull { session ->
            session.channel != "MESSAGE" && session.status in INCOMING_STATUSES
        }
        if (ringing == null) {
            val currentLocal = repository.getCurrent()
            if (currentLocal != null && currentLocal.direction == CallDirection.Incoming && currentLocal.runtimeState == CallRuntimeState.Connecting) {
                mutex.withLock {
                    val current = repository.getCurrent()
                    if (current != null && current.direction == CallDirection.Incoming && current.runtimeState == CallRuntimeState.Connecting) {
                        persistAndPresent(
                            current.copy(
                                runtimeState = CallRuntimeState.Finished,
                                updatedAtEpochMillis = nowMillis(),
                            ),
                        )
                        repository.clear()
                    }
                }
            }
            return
        }
        val currentLocal = repository.getCurrent()
        if (currentLocal != null && currentLocal.runtimeState.isActive() && currentLocal.expiresAtEpochMillis > nowMillis()) return
        ringIncoming(
            sessionId = ringing.id,
            elderId = ringing.elderId,
            channel = ringing.channel.ifBlank { "VOICE" },
        )
    }

    private suspend fun persistAndPresent(session: CallSession): AppResult<CallSession> {
        repository.saveCurrent(session)
        presentationGateway.onCallSession(session)
        return AppResult.Success(session)
    }

    private fun tagEventWithSession(event: CallMediaEvent, sessionId: String?): CallMediaEvent {
        if (sessionId == null) return event
        return when (event) {
            is CallMediaEvent.Joined -> if (event.sessionId == null) event.copy(sessionId = sessionId) else event
            is CallMediaEvent.Left -> if (event.sessionId == null) event.copy(sessionId = sessionId) else event
            is CallMediaEvent.ConnectionLost -> if (event.sessionId == null) event.copy(sessionId = sessionId) else event
            is CallMediaEvent.ConnectionRestored -> if (event.sessionId == null) event.copy(sessionId = sessionId) else event
        }
    }

    private companion object {
        val INCOMING_STATUSES = setOf("INITIATED", "CONNECTING", "CONNECTED")
        val TERMINAL_STATUSES = setOf("ENDED", "MISSED", "DECLINED", "FAILED", "CANCELLED")
    }
}
