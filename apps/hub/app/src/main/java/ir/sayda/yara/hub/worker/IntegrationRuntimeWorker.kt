package ir.sayda.yara.hub.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.ReconcileRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.data.device.HubDeviceStateReporter
import ir.sayda.yara.hub.data.identity.DataStoreReplicaIdentityProvider

@HiltWorker
class IntegrationRuntimeWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val runIntegrationCycleUseCase: RunIntegrationCycleUseCase,
    private val runSynchronizationCycleUseCase: RunSynchronizationCycleUseCase,
    private val recoverRuntimeUseCase: RecoverRuntimeUseCase,
    private val reconcileRuntimeUseCase: ReconcileRuntimeUseCase,
    private val provisioningGate: RuntimeProvisioningGate,
    private val identityProvider: DataStoreReplicaIdentityProvider,
    private val runtimeScheduler: RuntimeScheduler,
    private val hubDeviceStateReporter: HubDeviceStateReporter,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        identityProvider.hydrateFromStore()
        val ready = provisioningGate.requireRuntimeReady()
        if (!ready) {
            runtimeScheduler.scheduleRecurringSyncPoll()
            return Result.success()
        }

        hubDeviceStateReporter.reportOnline()

        val occurrenceId = inputData.getString(INPUT_OCCURRENCE_ID)
        val alarmTriggered = !occurrenceId.isNullOrBlank()

        if (alarmTriggered) {
            recoverRuntimeUseCase()
            val cycleResult = runIntegrationCycleUseCase()
            runtimeScheduler.scheduleRecurringSyncPoll()
            return when (cycleResult) {
                is AppResult.Success -> Result.success()
                is AppResult.Error -> Result.retry()
            }
        }

        val syncResult = runSynchronizationCycleUseCase("worker:${System.currentTimeMillis()}")
        recoverRuntimeUseCase()
        reconcileRuntimeUseCase()
        if (syncResult is AppResult.Error) {
            runtimeScheduler.scheduleRecurringSyncPoll()
            return Result.retry()
        }
        val cycleResult = runIntegrationCycleUseCase()
        runtimeScheduler.scheduleRecurringSyncPoll()
        return when (cycleResult) {
            is AppResult.Success -> Result.success()
            is AppResult.Error -> Result.retry()
        }
    }

    companion object {
        const val UNIQUE_WORK_NAME = "yara_integration_runtime"
        const val DELAYED_WORK_NAME = "yara_integration_runtime_delayed"
        const val PERIODIC_WORK_NAME = "yara_integration_runtime_periodic"
        const val POLL_WORK_NAME = "yara_integration_runtime_poll"
        const val INPUT_OCCURRENCE_ID = "occurrence_id"
    }
}
