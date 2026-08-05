package ir.sayda.yara.hub.core.runtime

data class OccurrenceAlarmSpec(
    val occurrenceId: String,
    val triggerAtEpochMillis: Long,
)

interface OccurrenceAlarmRegistry {
    suspend fun registerOccurrenceAlarm(spec: OccurrenceAlarmSpec)
    suspend fun cancelOccurrenceAlarm(occurrenceId: String)
    suspend fun restoreAlarms(specs: List<OccurrenceAlarmSpec>)
    fun isOccurrenceAlarmRegistered(occurrenceId: String): Boolean
    fun queryRegisteredOccurrenceIds(): Set<String>
}

interface ReminderNotificationGateway {
    suspend fun showReminderNotification(executionId: String, occurrenceId: String)
    fun cancelReminderNotification(executionId: String)
}

object AlarmRegistrationPlanner {
    fun filterFutureAlarms(specs: List<OccurrenceAlarmSpec>, nowEpochMillis: Long): List<OccurrenceAlarmSpec> =
        specs.filter { it.triggerAtEpochMillis > nowEpochMillis }

    fun dedupeByOccurrenceId(specs: List<OccurrenceAlarmSpec>): List<OccurrenceAlarmSpec> =
        specs
            .groupBy { it.occurrenceId }
            .map { (_, entries) -> entries.maxBy { it.triggerAtEpochMillis } }
}
