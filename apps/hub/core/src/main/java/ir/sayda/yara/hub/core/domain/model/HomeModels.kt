package ir.sayda.yara.hub.core.domain.model

data class TodayReminderItem(
    val occurrenceId: String,
    val executionId: String?,
    val title: String,
    val friendlyDescription: String,
    val scheduledForEpochMillis: Long,
    val status: String,
    val localConfirmationRecorded: Boolean = false,
)

data class ReminderPresentation(
    val executionId: String,
    val occurrenceId: String,
    val title: String,
    val friendlyDescription: String,
    val scheduledForEpochMillis: Long,
    val workflowStatus: String,
    val localConfirmationRecorded: Boolean = false,
)
