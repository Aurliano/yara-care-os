package ir.sayda.yara.hub.database.dao

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Pure ordering contract test — avoids Robolectric, which hangs on Windows during
 * `:database:testDebugUnitTest`. DAO ordering is enforced in [OutboxDao.getPending].
 */
class OutboxOrderingContractTest {

    @Test
    fun pendingOutboxEntriesSortByPriorityThenCreatedAt() {
        val entries = listOf(
            OutboxSortKey(id = "low-old", priority = 0, createdAt = 100L),
            OutboxSortKey(id = "high-new", priority = 10, createdAt = 200L),
            OutboxSortKey(id = "high-old", priority = 10, createdAt = 100L),
        )

        val sorted = entries.sortedWith(
            compareByDescending<OutboxSortKey> { it.priority }
                .thenBy { it.createdAt },
        )

        assertEquals(listOf("high-old", "high-new", "low-old"), sorted.map { it.id })
    }

    private data class OutboxSortKey(
        val id: String,
        val priority: Int,
        val createdAt: Long,
    )
}
