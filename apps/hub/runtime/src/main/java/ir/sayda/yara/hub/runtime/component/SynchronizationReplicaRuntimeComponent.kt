package ir.sayda.yara.hub.runtime.component

import ir.sayda.yara.hub.core.domain.repository.SyncSessionLocalRepository
import ir.sayda.yara.hub.core.runtime.RuntimeHealth
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SynchronizationReplicaRuntimeComponent @Inject constructor(
    private val syncSessionLocalRepository: SyncSessionLocalRepository,
) : BaseRuntimeComponent("synchronization_replica_runtime") {

    override suspend fun recover() {
        super.recover()
        syncSessionLocalRepository.getActive()
    }

    override suspend fun health(): RuntimeHealth {
        val activeSession = syncSessionLocalRepository.getActive()
        return RuntimeHealth(
            healthy = phase != ComponentPhase.STOPPED,
            state = if (activeSession != null) "SYNC_SESSION_ACTIVE" else phase.name,
            detail = activeSession?.sessionId ?: componentId,
        )
    }
}
