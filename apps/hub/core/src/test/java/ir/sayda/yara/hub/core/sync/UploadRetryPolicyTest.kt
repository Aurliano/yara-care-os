package ir.sayda.yara.hub.core.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class UploadRetryPolicyTest {

    @Test
    fun pendingIsAlwaysReady() {
        assertTrue(
            UploadRetryPolicy.isReady(
                status = "PENDING",
                retryCount = 0,
                lastAttemptAtEpochMillis = null,
                nowEpochMillis = 0L,
            ),
        )
    }

    @Test
    fun failedWaitsForBackoff() {
        val now = 120_000L
        assertFalse(
            UploadRetryPolicy.isReady(
                status = "FAILED",
                retryCount = 1,
                lastAttemptAtEpochMillis = now - 10_000L,
                nowEpochMillis = now,
            ),
        )
        assertTrue(
            UploadRetryPolicy.isReady(
                status = "FAILED",
                retryCount = 1,
                lastAttemptAtEpochMillis = now - 60_000L,
                nowEpochMillis = now,
            ),
        )
    }

    @Test
    fun exhaustedFailedIsNotRetried() {
        assertFalse(
            UploadRetryPolicy.isReady(
                status = "FAILED",
                retryCount = UploadRetryPolicy.MAX_RETRIES,
                lastAttemptAtEpochMillis = 0L,
                nowEpochMillis = Long.MAX_VALUE,
            ),
        )
    }

    @Test
    fun backoffCapsAtFifteenMinutes() {
        assertEquals(30_000L, UploadRetryPolicy.backoffMs(0))
        assertEquals(60_000L, UploadRetryPolicy.backoffMs(1))
        assertEquals(UploadRetryPolicy.MAX_BACKOFF_MS, UploadRetryPolicy.backoffMs(9))
        assertEquals(UploadRetryPolicy.MAX_BACKOFF_MS, UploadRetryPolicy.backoffMs(20))
    }
}
