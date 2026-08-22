package ir.sayda.yara.hub.core.domain.model

data class TodayReminderItem(
    val occurrenceId: String,
    val executionId: String?,
    val title: String,
    val friendlyDescription: String,
    val scheduledForEpochMillis: Long,
    val status: String,
    val localConfirmationRecorded: Boolean = false,
    val confirmedAtEpochMillis: Long? = null,
)

/**
 * The elder screen must stay calm, so a dose leaves the list a short while
 * after it is confirmed. Only the UI hides it; the replica rows stay for
 * history and upload.
 */
object TodayReminderVisibility {
    const val CONFIRMED_VISIBILITY_MS: Long = 15 * 60 * 1000L

    fun isVisible(item: TodayReminderItem, nowEpochMillis: Long): Boolean {
        val confirmedAt = item.confirmedAtEpochMillis ?: return true
        return nowEpochMillis - confirmedAt < CONFIRMED_VISIBILITY_MS
    }

    fun visibleAt(items: List<TodayReminderItem>, nowEpochMillis: Long): List<TodayReminderItem> =
        items.filter { isVisible(it, nowEpochMillis) }
}

data class ReminderPresentation(
    val executionId: String,
    val occurrenceId: String,
    val title: String,
    val friendlyDescription: String,
    val scheduledForEpochMillis: Long,
    val workflowStatus: String,
    val localConfirmationRecorded: Boolean = false,
    val postponeAllowed: Boolean = false,
    val remainingPostpones: Int = 0,
    val postponeDelayMinutes: Int = 0,
)
