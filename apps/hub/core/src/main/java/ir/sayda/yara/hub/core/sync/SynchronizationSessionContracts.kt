package ir.sayda.yara.hub.core.sync

import ir.sayda.yara.hub.core.result.AppResult

data class ActiveSynchronizationSession(
    val sessionId: String,
    val direction: SyncDirection,
    val status: SyncSessionStatus,
)

interface SynchronizationClient {
    suspend fun beginSession(
        direction: SyncDirection,
        idempotencyKey: String,
    ): AppResult<ActiveSynchronizationSession>

    suspend fun upload(limit: Int = 25): AppResult<Int>

    suspend fun download(): AppResult<Unit>

    suspend fun complete(): AppResult<Unit>

    suspend fun cancel(): AppResult<Unit>

    suspend fun resume(): AppResult<ActiveSynchronizationSession>

    suspend fun flushPendingEvidence(limit: Int = 25): AppResult<Int>
}
