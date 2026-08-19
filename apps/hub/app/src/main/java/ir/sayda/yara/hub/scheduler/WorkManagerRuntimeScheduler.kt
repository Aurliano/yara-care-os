package ir.sayda.yara.hub.scheduler

import android.content.Context
import androidx.work.Data
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.worker.IntegrationRuntimeWorker
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WorkManagerRuntimeScheduler @Inject constructor(
    @ApplicationContext private val context: Context,
) : RuntimeScheduler {

    override fun schedulePeriodicRuntimeWork() {
        val request = PeriodicWorkRequestBuilder<IntegrationRuntimeWorker>(15, TimeUnit.MINUTES).build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            IntegrationRuntimeWorker.PERIODIC_WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }

    override fun scheduleOneTimeRuntimeWork(occurrenceId: String?) {
        enqueueRuntimeWork(occurrenceId = occurrenceId, delayMs = 0L)
    }

    override fun scheduleDelayedRuntimeWork(occurrenceId: String, delayMs: Long) {
        enqueueRuntimeWork(occurrenceId = occurrenceId, delayMs = delayMs)
    }

    override fun scheduleRecurringSyncPoll(delayMs: Long) {
        val request = OneTimeWorkRequestBuilder<IntegrationRuntimeWorker>()
            .setInitialDelay(delayMs.coerceAtLeast(1L), TimeUnit.MILLISECONDS)
            .build()
        WorkManager.getInstance(context).enqueueUniqueWork(
            IntegrationRuntimeWorker.POLL_WORK_NAME,
            ExistingWorkPolicy.REPLACE,
            request,
        )
    }

    private fun enqueueRuntimeWork(occurrenceId: String?, delayMs: Long) {
        val input = if (occurrenceId.isNullOrBlank()) {
            Data.EMPTY
        } else {
            Data.Builder()
                .putString(IntegrationRuntimeWorker.INPUT_OCCURRENCE_ID, occurrenceId)
                .build()
        }
        val requestBuilder = OneTimeWorkRequestBuilder<IntegrationRuntimeWorker>()
            .setInputData(input)
        if (delayMs > 0L) {
            requestBuilder.setInitialDelay(delayMs, TimeUnit.MILLISECONDS)
        }
        val workName = if (delayMs > 0L) {
            IntegrationRuntimeWorker.DELAYED_WORK_NAME
        } else {
            IntegrationRuntimeWorker.UNIQUE_WORK_NAME
        }
        WorkManager.getInstance(context).enqueueUniqueWork(
            workName,
            ExistingWorkPolicy.REPLACE,
            requestBuilder.build(),
        )
    }
}
