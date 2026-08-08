package ir.sayda.yara.hub.data.repository

import androidx.room.withTransaction
import ir.sayda.yara.hub.core.sync.SyncApplyTransaction
import ir.sayda.yara.hub.database.HubDatabase
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncApplyTransactionImpl @Inject constructor(
    private val database: HubDatabase,
) : SyncApplyTransaction {

    override suspend fun <T> withReplicaMutation(
        checkpointSequence: Long,
        checkpointToken: String?,
        block: suspend () -> T,
    ): T = database.withTransaction {
        val result = block()
        val current = database.replicaStateDao().get() ?: return@withTransaction result
        if (checkpointSequence > current.checkpointSequence) {
            database.replicaStateDao().upsert(
                current.copy(
                    checkpointSequence = checkpointSequence,
                    checkpointToken = checkpointToken,
                    lastSuccessfulSyncEpochMillis = System.currentTimeMillis(),
                ),
            )
        }
        result
    }
}
