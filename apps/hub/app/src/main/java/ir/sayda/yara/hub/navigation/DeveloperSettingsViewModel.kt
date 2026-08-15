package ir.sayda.yara.hub.navigation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.bootstrap.HubWorkflowBootstrap
import java.util.Calendar
import javax.inject.Inject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@HiltViewModel
class DeveloperSettingsViewModel @Inject constructor(
    private val runtimeScheduler: RuntimeScheduler,
    private val schedulingRepository: SchedulingReplicaRepository,
    private val runtimeAlarmCoordinator: RuntimeAlarmCoordinator,
    private val hubWorkflowBootstrap: HubWorkflowBootstrap,
) : ViewModel() {
    fun forceSynchronization() {
        runtimeScheduler.scheduleOneTimeRuntimeWork()
    }

    /** Moves the soonest today occurrence to one minute from now and arms alarm + worker backup. */
    fun scheduleTestReminderInOneMinute() {
        viewModelScope.launch(Dispatchers.IO) {
            val now = System.currentTimeMillis()
            val triggerAt = now + TEST_REMINDER_DELAY_MS
            val endOfDay = endOfTodayEpochMillis()

            val due = schedulingRepository.getOccurrencesDueBefore(now)
            val scheduledPastDue = schedulingRepository.getScheduledOccurrencesDueBefore(now)
            val scheduledFutureToday = schedulingRepository.getScheduledOccurrencesAfter(now)
                .filter {
                    it.status == OccurrenceStatus.SCHEDULED.name &&
                        it.scheduledForEpochMillis <= endOfDay
                }
            var candidates = (due + scheduledPastDue + scheduledFutureToday)
                .distinctBy { it.id }
            if (candidates.isEmpty()) {
                candidates = schedulingRepository.getScheduledOccurrencesAfter(0)
                    .filter { it.status == OccurrenceStatus.SCHEDULED.name }
                    .take(1)
            }
            if (candidates.isEmpty()) {
                ir.sayda.yara.hub.core.debug.DebugTrace.log(
                    "DEV",
                    "DeveloperSettingsViewModel.kt:scheduleTest",
                    "no candidates for local test",
                    mapOf(
                        "dueCount" to due.size,
                        "scheduledPastDueCount" to scheduledPastDue.size,
                        "scheduledFutureTodayCount" to scheduledFutureToday.size,
                    ),
                )
                return@launch
            }

            hubWorkflowBootstrap.ensureWorkflowDefinitionsForCareActivities()

            candidates.forEach { occurrence ->
                schedulingRepository.upsertOccurrence(
                    occurrence.copy(
                        scheduledForEpochMillis = triggerAt,
                        status = OccurrenceStatus.SCHEDULED.name,
                        updatedAtEpochMillis = now,
                    ),
                )
                runtimeAlarmCoordinator.cancelAlarmForOccurrence(occurrence.id)
            }
            val primary = candidates.minByOrNull { it.scheduledForEpochMillis }!!
            runtimeAlarmCoordinator.registerAlarmForOccurrence(
                occurrenceId = primary.id,
                triggerAtEpochMillis = triggerAt,
                nowEpochMillis = now,
            )
            ir.sayda.yara.hub.core.debug.DebugTrace.log(
                "DEV",
                "DeveloperSettingsViewModel.kt:scheduleTest",
                "local test reminder scheduled",
                mapOf(
                    "occurrenceId" to primary.id,
                    "rescheduledCount" to candidates.size,
                    "triggerAt" to triggerAt,
                ),
            )
            runtimeScheduler.scheduleDelayedRuntimeWork(
                occurrenceId = primary.id,
                delayMs = TEST_REMINDER_DELAY_MS,
            )
        }
    }

    companion object {
        private const val TEST_REMINDER_DELAY_MS = 60_000L
    }

    private fun endOfTodayEpochMillis(): Long {
        val calendar = Calendar.getInstance()
        calendar.set(Calendar.HOUR_OF_DAY, 23)
        calendar.set(Calendar.MINUTE, 59)
        calendar.set(Calendar.SECOND, 59)
        calendar.set(Calendar.MILLISECOND, 999)
        return calendar.timeInMillis
    }
}
