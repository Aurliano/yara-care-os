package ir.sayda.yara.hub.core.sync

import ir.sayda.yara.hub.core.result.AppResult

data class ActiveSynchronizationSession(
    val sessionId: String,
    val direction: SyncDirection,
    val status: SyncSessionStatus,
    val synchronizationToken: String? = null,
)

interface SynchronizationClient {
    suspend fun beginDownloadSession(idempotencyKey: String): AppResult<ActiveSynchronizationSession>

    suspend fun beginUploadSession(idempotencyKey: String): AppResult<ActiveSynchronizationSession>

    suspend fun downloadChanges(): AppResult<List<SyncOperation>>

    suspend fun downloadSnapshot(): AppResult<List<SyncOperation>>

    suspend fun applyChanges(operations: List<SyncOperation>): AppResult<ApplySummary>

    suspend fun advanceCheckpoint(token: String?): AppResult<Unit>

    suspend fun uploadPendingEvidence(limit: Int = 25): AppResult<Int>

    suspend fun uploadOutbox(limit: Int = 25): AppResult<Int>

    suspend fun resume(): AppResult<ActiveSynchronizationSession>

    suspend fun cancel(): AppResult<Unit>

    suspend fun complete(): AppResult<Unit>

    suspend fun runSynchronizationCycle(idempotencyKey: String): AppResult<ApplySummary>
}
