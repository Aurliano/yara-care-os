package ir.sayda.yara.hub.core.domain.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TodayReminderVisibilityTest {

    private val now = 1_000_000_000L

    private fun reminder(id: String, confirmedAt: Long?) = TodayReminderItem(
        occurrenceId = id,
        executionId = "exec-$id",
        title = "دارو صبح",
        friendlyDescription = "یک قرص",
        scheduledForEpochMillis = now - 60_000L,
        status = "DUE",
        localConfirmationRecorded = confirmedAt != null,
        confirmedAtEpochMillis = confirmedAt,
    )

    @Test
    fun unconfirmedReminderStaysVisible() {
        assertTrue(TodayReminderVisibility.isVisible(reminder("a", confirmedAt = null), now))
    }

    @Test
    fun justConfirmedReminderStaysVisibleSoTheElderSeesTheTick() {
        assertTrue(TodayReminderVisibility.isVisible(reminder("a", confirmedAt = now - 1_000L), now))
    }

    @Test
    fun confirmedReminderDisappearsAfterFifteenMinutes() {
        val fifteenMinutesAgo = now - TodayReminderVisibility.CONFIRMED_VISIBILITY_MS
        assertFalse(TodayReminderVisibility.isVisible(reminder("a", confirmedAt = fifteenMinutesAgo), now))
        assertTrue(
            TodayReminderVisibility.isVisible(reminder("a", confirmedAt = fifteenMinutesAgo + 1L), now),
        )
    }

    @Test
    fun onlyExpiredConfirmationsAreFilteredOut() {
        val items = listOf(
            reminder("fresh", confirmedAt = now - 60_000L),
            reminder("stale", confirmedAt = now - TodayReminderVisibility.CONFIRMED_VISIBILITY_MS - 1L),
            reminder("open", confirmedAt = null),
        )

        val visible = TodayReminderVisibility.visibleAt(items, now).map { it.occurrenceId }

        assertEquals(listOf("fresh", "open"), visible)
    }
}
