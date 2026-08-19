package ir.sayda.yara.hub

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import ir.sayda.yara.hub.connectivity.ConnectivitySyncTrigger
import ir.sayda.yara.hub.core.domain.usecase.ReconcileRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.data.identity.DataStoreReplicaIdentityProvider
import ir.sayda.yara.hub.provisioning.HubProvisioningCoordinator
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

@HiltAndroidApp
class YaraApplication : Application(), Configuration.Provider {

    @Inject lateinit var workerFactory: HiltWorkerFactory
    @Inject lateinit var identityProvider: DataStoreReplicaIdentityProvider
    @Inject lateinit var recoverRuntimeUseCase: RecoverRuntimeUseCase
    @Inject lateinit var reconcileRuntimeUseCase: ReconcileRuntimeUseCase
    @Inject lateinit var runtimeScheduler: RuntimeScheduler
    @Inject lateinit var connectivitySyncTrigger: ConnectivitySyncTrigger
    @Inject lateinit var provisioningCoordinator: HubProvisioningCoordinator
    @Inject lateinit var provisioningGate: RuntimeProvisioningGate
    @Inject lateinit var runSynchronizationCycleUseCase: RunSynchronizationCycleUseCase

    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        applicationScope.launch {
            identityProvider.hydrateFromStore()
            provisioningCoordinator.start(applicationScope)
            provisioningGate.observeRuntimeAllowed()
                .filter { allowed -> allowed }
                .first()
            startRuntimeServices()
        }
    }

    private suspend fun startRuntimeServices() {
        val syncResult = runSynchronizationCycleUseCase("app-start:${System.currentTimeMillis()}")
        recoverRuntimeUseCase()
        if (syncResult is AppResult.Success && !syncResult.data.hasAppliedChanges) {
            reconcileRuntimeUseCase()
        }
        runtimeScheduler.schedulePeriodicRuntimeWork()
        runtimeScheduler.scheduleRecurringSyncPoll()
        connectivitySyncTrigger.register()
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
}
