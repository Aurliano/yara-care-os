package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ReplicaStateInitializer @Inject constructor(
    private val replicaMetadataRepository: ReplicaMetadataRepository,
    private val authRepository: AuthRepository,
) {
    suspend fun ensureInitialized() {
        if (replicaMetadataRepository.getReplicaState() != null) return
        val identity = authRepository.getIdentity() ?: return
        if (identity.provisioningState != ProvisioningState.READY) return
        replicaMetadataRepository.upsertReplicaState(
            ReplicaState(
                replicaIdentifier = identity.replicaId,
                replicaType = "HUB",
                health = "UNKNOWN",
                status = "ACTIVE",
                checkpointSequence = 0L,
                checkpointToken = null,
                lastSuccessfulSyncEpochMillis = null,
            ),
        )
    }
}
