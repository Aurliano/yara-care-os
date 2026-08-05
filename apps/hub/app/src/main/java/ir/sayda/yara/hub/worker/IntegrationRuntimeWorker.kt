package ir.sayda.yara.hub.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.result.AppResult

@HiltWorker
class IntegrationRuntimeWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val runIntegrationCycleUseCase: RunIntegrationCycleUseCase,
    private val recoverRuntimeUseCase: RecoverRuntimeUseCase,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        recoverRuntimeUseCase()
        return when (val cycle = runIntegrationCycleUseCase()) {
            is AppResult.Success -> Result.success()
            is AppResult.Error -> Result.retry()
        }
    }

    companion object {
        const val UNIQUE_WORK_NAME = "yara_integration_runtime"
        const val PERIODIC_WORK_NAME = "yara_integration_runtime_periodic"
    }
}
