package ir.sayda.yara.hub.core.sync

interface SyncApplyTransaction {
    suspend fun <T> withReplicaMutation(
        checkpointSequence: Long,
        checkpointToken: String?,
        block: suspend () -> T,
    ): T
}
