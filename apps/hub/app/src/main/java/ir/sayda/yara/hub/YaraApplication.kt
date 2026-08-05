package ir.sayda.yara.hub

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import ir.sayda.yara.hub.connectivity.ConnectivitySyncTrigger
import ir.sayda.yara.hub.data.identity.DataStoreReplicaIdentityProvider
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.runtime.HubRuntimeOrchestrator
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

@HiltAndroidApp
class YaraApplication : Application(), Configuration.Provider {

    @Inject lateinit var workerFactory: HiltWorkerFactory
    @Inject lateinit var identityProvider: DataStoreReplicaIdentityProvider
    @Inject lateinit var runtimeOrchestrator: HubRuntimeOrchestrator
    @Inject lateinit var runtimeScheduler: RuntimeScheduler
    @Inject lateinit var connectivitySyncTrigger: ConnectivitySyncTrigger

    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        applicationScope.launch {
            identityProvider.hydrateFromStore()
            runtimeOrchestrator.recover()
            runtimeScheduler.schedulePeriodicRuntimeWork()
            connectivitySyncTrigger.register()
        }
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
}
