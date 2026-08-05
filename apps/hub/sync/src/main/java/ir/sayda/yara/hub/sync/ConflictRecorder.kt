package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.SyncConflictRepository
import ir.sayda.yara.hub.core.sync.ConflictType
import ir.sayda.yara.hub.core.sync.SyncConflictRecord
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConflictRecorder @Inject constructor(
    private val syncConflictRepository: SyncConflictRepository,
) {
    suspend fun recordVersionMismatch(
        aggregateReference: String,
        localVersion: String?,
        remoteVersion: String,
        sessionId: String?,
        payloadJson: String,
    ) {
        syncConflictRepository.record(
            SyncConflictRecord(
                id = UUID.randomUUID().toString(),
                aggregateReference = aggregateReference,
                conflictType = ConflictType.VERSION_MISMATCH,
                localVersion = localVersion,
                remoteVersion = remoteVersion,
                sessionId = sessionId,
                detectedAtEpochMillis = System.currentTimeMillis(),
                payloadJson = payloadJson,
            ),
        )
    }
}
