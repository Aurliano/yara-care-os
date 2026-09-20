package ir.sayda.yara.hub.worker

import android.content.Context
import androidx.hilt.work.HiltWorkerFactoryTestAccess
import androidx.hilt.work.WorkerAssistedFactory
import androidx.work.ListenableWorker
import androidx.work.WorkerParameters
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.ReconcileRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.core.sync.ApplySummary
import ir.sayda.yara.hub.data.device.HubDeviceStateReporter
import ir.sayda.yara.hub.data.identity.DataStoreReplicaIdentityProvider
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import javax.inject.Provider

class IntegrationRuntimeWorkerTest {

    private val runIntegrationCycleUseCase: RunIntegrationCycleUseCase = mockk(relaxed = true)
    private val runSynchronizationCycleUseCase: RunSynchronizationCycleUseCase = mockk(relaxed = true)
    private val recoverRuntimeUseCase: RecoverRuntimeUseCase = mockk(relaxed = true)
    private val reconcileRuntimeUseCase: ReconcileRuntimeUseCase = mockk(relaxed = true)
    private val provisioningGate: RuntimeProvisioningGate = mockk(relaxed = true)
    private val identityProvider: DataStoreReplicaIdentityProvider = mockk(relaxed = true)
    private val runtimeScheduler: RuntimeScheduler = mockk(relaxed = true)
    private val hubDeviceStateReporter: HubDeviceStateReporter = mockk(relaxed = true)

    private val context: Context = mockk(relaxed = true)
    private val workerParams: WorkerParameters = mockk(relaxed = true)

    @Test
    fun hiltWorkerFactory_instantiatesWorker_withoutNoSuchMethodException() {
        val assistedFactory = object : IntegrationRuntimeWorker_AssistedFactory {
            override fun create(appContext: Context, workerParams: WorkerParameters): IntegrationRuntimeWorker {
                return IntegrationRuntimeWorker(
                    appContext = appContext,
                    workerParams = workerParams,
                    runIntegrationCycleUseCase = runIntegrationCycleUseCase,
                    runSynchronizationCycleUseCase = runSynchronizationCycleUseCase,
                    recoverRuntimeUseCase = recoverRuntimeUseCase,
                    reconcileRuntimeUseCase = reconcileRuntimeUseCase,
                    provisioningGate = provisioningGate,
                    identityProvider = identityProvider,
                    runtimeScheduler = runtimeScheduler,
                    hubDeviceStateReporter = hubDeviceStateReporter,
                )
            }
        }

        val workerFactories = mapOf<String, Provider<WorkerAssistedFactory<out ListenableWorker>>>(
            IntegrationRuntimeWorker::class.java.name to Provider { assistedFactory }
        )

        val hiltWorkerFactory = HiltWorkerFactoryTestAccess.create(workerFactories)
        val worker = hiltWorkerFactory.createWorker(context, IntegrationRuntimeWorker::class.java.name, workerParams)

        assertNotNull("Worker should be created by HiltWorkerFactory", worker)
        assertTrue("Created worker must be IntegrationRuntimeWorker", worker is IntegrationRuntimeWorker)
    }

    @Test
    fun integrationRuntimeWorker_executesSynchronization_whenRuntimeReady() = runBlocking {
        val summary = ApplySummary(appliedCount = 1, skippedCount = 0, conflictCount = 0, affectedReplicaDomains = emptySet())
        coEvery { provisioningGate.requireRuntimeReady() } returns true
        coEvery { runSynchronizationCycleUseCase.invoke(any()) } returns AppResult.Success(summary)
        coEvery { runIntegrationCycleUseCase.invoke() } returns AppResult.Success(emptyMap())

        val worker = IntegrationRuntimeWorker(
            appContext = context,
            workerParams = workerParams,
            runIntegrationCycleUseCase = runIntegrationCycleUseCase,
            runSynchronizationCycleUseCase = runSynchronizationCycleUseCase,
            recoverRuntimeUseCase = recoverRuntimeUseCase,
            reconcileRuntimeUseCase = reconcileRuntimeUseCase,
            provisioningGate = provisioningGate,
            identityProvider = identityProvider,
            runtimeScheduler = runtimeScheduler,
            hubDeviceStateReporter = hubDeviceStateReporter,
        )

        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        coVerify(exactly = 1) { identityProvider.hydrateFromStore() }
        coVerify(exactly = 1) { provisioningGate.requireRuntimeReady() }
        coVerify(exactly = 1) { hubDeviceStateReporter.reportOnline() }
        coVerify(exactly = 1) { runSynchronizationCycleUseCase.invoke(any()) }
        coVerify(exactly = 1) { recoverRuntimeUseCase.invoke() }
        coVerify(exactly = 1) { reconcileRuntimeUseCase.invoke() }
    }

    @Test
    fun integrationRuntimeWorker_handlesNotReady_withoutCrashing() = runBlocking {
        coEvery { provisioningGate.requireRuntimeReady() } returns false

        val worker = IntegrationRuntimeWorker(
            appContext = context,
            workerParams = workerParams,
            runIntegrationCycleUseCase = runIntegrationCycleUseCase,
            runSynchronizationCycleUseCase = runSynchronizationCycleUseCase,
            recoverRuntimeUseCase = recoverRuntimeUseCase,
            reconcileRuntimeUseCase = reconcileRuntimeUseCase,
            provisioningGate = provisioningGate,
            identityProvider = identityProvider,
            runtimeScheduler = runtimeScheduler,
            hubDeviceStateReporter = hubDeviceStateReporter,
        )

        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        coVerify(exactly = 0) { runSynchronizationCycleUseCase.invoke(any()) }
        coVerify(exactly = 1) { runtimeScheduler.scheduleRecurringSyncPoll() }
    }
}
