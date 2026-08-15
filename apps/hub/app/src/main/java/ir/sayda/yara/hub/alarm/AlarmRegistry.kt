package ir.sayda.yara.hub.alarm

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmRegistry
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmSpec
import ir.sayda.yara.hub.runtime.alarm.stableAlarmRequestCode
import java.util.concurrent.ConcurrentHashMap
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AlarmRegistry @Inject constructor(
    @ApplicationContext private val context: Context,
) : OccurrenceAlarmRegistry {

    private val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
    private val trackedOccurrenceIds = ConcurrentHashMap.newKeySet<String>()

    override suspend fun registerOccurrenceAlarm(spec: OccurrenceAlarmSpec) {
        if (spec.triggerAtEpochMillis <= System.currentTimeMillis()) {
            cancelOccurrenceAlarm(spec.occurrenceId)
            return
        }

        // Always cancel first so trigger-time updates are not blocked by a stale PendingIntent.
        alarmManager.cancel(pendingIntentFor(spec.occurrenceId))
        trackedOccurrenceIds.remove(spec.occurrenceId)

        alarmManager.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            spec.triggerAtEpochMillis,
            pendingIntentFor(spec.occurrenceId),
        )
        trackedOccurrenceIds.add(spec.occurrenceId)
    }

    override suspend fun cancelOccurrenceAlarm(occurrenceId: String) {
        alarmManager.cancel(pendingIntentFor(occurrenceId))
        trackedOccurrenceIds.remove(occurrenceId)
    }

    override suspend fun restoreAlarms(specs: List<OccurrenceAlarmSpec>) {
        val desiredIds = specs.map { it.occurrenceId }.toSet()
        trackedOccurrenceIds
            .filter { it !in desiredIds }
            .forEach { cancelOccurrenceAlarm(it) }
        specs.forEach { registerOccurrenceAlarm(it) }
    }

    override fun isOccurrenceAlarmRegistered(occurrenceId: String): Boolean {
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            stableAlarmRequestCode(occurrenceId),
            alarmIntent(occurrenceId),
            PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE,
        )
        return pendingIntent != null
    }

    override fun queryRegisteredOccurrenceIds(): Set<String> {
        val active = trackedOccurrenceIds.filterTo(mutableSetOf()) { isOccurrenceAlarmRegistered(it) }
        trackedOccurrenceIds.clear()
        trackedOccurrenceIds.addAll(active)
        return active.toSet()
    }

    private fun pendingIntentFor(occurrenceId: String): PendingIntent =
        PendingIntent.getBroadcast(
            context,
            stableAlarmRequestCode(occurrenceId),
            alarmIntent(occurrenceId),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

    private fun alarmIntent(occurrenceId: String): Intent =
        Intent(context, OccurrenceAlarmReceiver::class.java).apply {
            action = OccurrenceAlarmReceiver.ACTION_OCCURRENCE_ALARM
            putExtra(OccurrenceAlarmReceiver.EXTRA_OCCURRENCE_ID, occurrenceId)
        }
}
