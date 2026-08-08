package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.model.SyncSession
import ir.sayda.yara.hub.core.domain.repository.SyncSessionLocalRepository
import ir.sayda.yara.hub.core.sync.ActiveSynchronizationSession
import ir.sayda.yara.hub.core.sync.SyncDirection
import ir.sayda.yara.hub.core.sync.SyncSessionStatus
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncSessionStore @Inject constructor(
    private val syncSessionLocalRepository: SyncSessionLocalRepository,
) {
    private var cachedSession: ActiveSynchronizationSession? = null

    fun getCached(): ActiveSynchronizationSession? = cachedSession

    suspend fun restoreActive(): ActiveSynchronizationSession? {
        cachedSession?.let { return it }
        val persisted = syncSessionLocalRepository.getActive() ?: return null
        return persisted.toActive().also { cachedSession = it }
    }

    suspend fun persist(session: SyncSession, status: SyncSessionStatus) {
        syncSessionLocalRepository.save(
            session.copy(status = status.name),
        )
        cachedSession = ActiveSynchronizationSession(
            sessionId = session.sessionId,
            direction = SyncDirection.valueOf(session.direction),
            status = status,
            synchronizationToken = session.synchronizationToken,
        )
    }

    suspend fun updateStatus(status: SyncSessionStatus) {
        val current = cachedSession ?: return
        cachedSession = current.copy(status = status)
        syncSessionLocalRepository.updateStatus(current.sessionId, status.name)
    }

    suspend fun completeAndRetain(status: SyncSessionStatus) {
        val current = cachedSession ?: return
        syncSessionLocalRepository.updateStatus(current.sessionId, status.name)
        cachedSession = null
    }

    suspend fun clear() {
        cachedSession?.sessionId?.let { syncSessionLocalRepository.clear(it) }
        cachedSession = null
    }

    private fun SyncSession.toActive() = ActiveSynchronizationSession(
        sessionId = sessionId,
        direction = SyncDirection.valueOf(direction),
        status = runCatching { SyncSessionStatus.valueOf(status) }
            .getOrDefault(SyncSessionStatus.SESSION_STARTED),
        synchronizationToken = synchronizationToken,
    )
}
