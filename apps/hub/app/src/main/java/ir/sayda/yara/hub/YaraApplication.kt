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
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
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
    @Inject lateinit var communicationRuntime: ir.sayda.yara.hub.runtime.communication.CommunicationRuntime

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
        runCatching { runSynchronizationCycleUseCase("app-start:${System.currentTimeMillis()}") }
        recoverRuntimeUseCase()
        reconcileRuntimeUseCase()
        runtimeScheduler.schedulePeriodicRuntimeWork()
        runtimeScheduler.scheduleRecurringSyncPoll()
        connectivitySyncTrigger.register()
        communicationRuntime.startIncomingCallPoller()
        startForegroundSyncLoop()
    }

    private fun startForegroundSyncLoop() {
        applicationScope.launch {
            while (isActive) {
                delay(FOREGROUND_SYNC_INTERVAL_MS)
                runCatching {
                    runSynchronizationCycleUseCase("foreground-poll:${System.currentTimeMillis()}")
                }
            }
        }
    }

    companion object {
        private const val FOREGROUND_SYNC_INTERVAL_MS = 30_000L
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
}
