package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository
import ir.sayda.yara.hub.core.result.AppResult
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CheckpointCoordinator @Inject constructor(
    private val replicaMetadataRepository: ReplicaMetadataRepository,
    private val synchronizationRepository: SynchronizationRepository,
    private val authRepository: AuthRepository,
) {
    suspend fun advanceFromRemote(token: String?): AppResult<Unit> {
        val replicaId = authRepository.getIdentity()?.replicaId
            ?: return AppResult.Error(IllegalStateException("Replica identity unavailable"))
        return when (val checkpoint = synchronizationRepository.fetchCheckpoint(replicaId)) {
            is AppResult.Success -> {
                replicaMetadataRepository.advanceCheckpoint(
                    sequence = checkpoint.data.checkpointSequence,
                    token = token ?: checkpoint.data.checkpointToken,
                )
                AppResult.Success(Unit)
            }
            is AppResult.Error -> checkpoint
        }
    }

    suspend fun advanceLocal(sequence: Long, token: String?) {
        replicaMetadataRepository.advanceCheckpoint(sequence, token)
    }
}
