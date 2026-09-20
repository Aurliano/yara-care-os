package androidx.hilt.work

import androidx.work.ListenableWorker
import javax.inject.Provider

object HiltWorkerFactoryTestAccess {
    fun create(
        factories: Map<String, Provider<WorkerAssistedFactory<out ListenableWorker>>>
    ): HiltWorkerFactory {
        return HiltWorkerFactory(factories)
    }
}
