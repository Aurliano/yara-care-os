package ir.sayda.yara.hub.core.sync

/**
 * Failed Hub uploads used to stay FAILED forever. Retry them with a bounded
 * backoff so a confirmation that the cloud was not ready for (404) can land
 * on the next cycle instead of vanishing.
 */
object UploadRetryPolicy {
    const val MAX_RETRIES = 8
    const val BASE_BACKOFF_MS = 30_000L
    const val MAX_BACKOFF_MS = 15 * 60 * 1_000L

    fun backoffMs(retryCount: Int): Long {
        val shifts = retryCount.coerceAtLeast(0).coerceAtMost(9)
        return (BASE_BACKOFF_MS shl shifts).coerceAtMost(MAX_BACKOFF_MS)
    }

    fun isReady(
        status: String,
        retryCount: Int,
        lastAttemptAtEpochMillis: Long?,
        nowEpochMillis: Long,
    ): Boolean {
        if (status == "PENDING") return true
        if (status != "FAILED") return false
        if (retryCount >= MAX_RETRIES) return false
        val lastAttempt = lastAttemptAtEpochMillis ?: 0L
        return nowEpochMillis - lastAttempt >= backoffMs(retryCount)
    }
}
