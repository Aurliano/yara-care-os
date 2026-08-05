package ir.sayda.yara.hub.runtime

import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.IntegrationRuntimeRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.IllegalRuntimeTransitionException
import ir.sayda.yara.hub.core.runtime.RuntimeKernel
import ir.sayda.yara.hub.core.runtime.RuntimeKernelState
import ir.sayda.yara.hub.core.sync.SyncDirection
import ir.sayda.yara.hub.core.sync.SynchronizationClient
import ir.sayda.yara.hub.runtime.component.CommunicationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.DeviceReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.IntegrationRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SchedulingReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SynchronizationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.WorkflowReplicaRuntimeComponent
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HubRuntimeOrchestrator @Inject constructor(
    private val runtimeKernel: RuntimeKernel,
    private val integrationRuntimeRepository: IntegrationRuntimeRepository,
    private val schedulingReplicaRepository: SchedulingReplicaRepository,
    private val synchronizationClient: SynchronizationClient,
    private val authRepository: AuthRepository,
    private val connectivityRepository: ConnectivityRepository,
    private val schedulingRuntime: SchedulingReplicaRuntimeComponent,
    private val workflowRuntime: WorkflowReplicaRuntimeComponent,
    private val synchronizationRuntime: SynchronizationReplicaRuntimeComponent,
    private val deviceRuntime: DeviceReplicaRuntimeComponent,
    private val communicationRuntime: CommunicationReplicaRuntimeComponent,
    private val integrationRuntime: IntegrationRuntimeComponent,
) {

    private var componentsRegistered = false

    private fun registerComponentsIfNeeded() {
        if (componentsRegistered) return
        runtimeKernel.register(schedulingRuntime)
        runtimeKernel.register(workflowRuntime)
        runtimeKernel.register(synchronizationRuntime)
        runtimeKernel.register(deviceRuntime)
        runtimeKernel.register(communicationRuntime)
        runtimeKernel.register(integrationRuntime)
        componentsRegistered = true
    }

    suspend fun recover(): AppResult<Unit> {
        return try {
            ensureRunningKernel()
            AppResult.Success(Unit)
        } catch (exception: IllegalRuntimeTransitionException) {
            AppResult.Error(exception)
        }
    }

    suspend fun runCycle(): AppResult<Map<String, Int>> {
        try {
            ensureRunningKernel()
        } catch (exception: IllegalRuntimeTransitionException) {
            return AppResult.Error(exception)
        }

        authRepository.refreshTokenIfNeeded()

        val localDue = schedulingReplicaRepository.getOccurrencesDueBefore(System.currentTimeMillis()).size

        val remoteResult = if (connectivityRepository.isOnline()) {
            integrationRuntimeRepository.processRuntimeCycle()
        } else {
            AppResult.Success(
                mapOf(
                    "due_occurrences" to localDue,
                    "workflow_timeouts" to 0,
                    "events_processed" to 0,
                ),
            )
        }

        if (connectivityRepository.isOnline()) {
            when (synchronizationClient.beginSession(SyncDirection.UPLOAD, UUID.randomUUID().toString())) {
                is AppResult.Success -> {
                    synchronizationClient.upload(limit = 25)
                    synchronizationClient.flushPendingEvidence(limit = 25)
                    synchronizationClient.complete()
                }
                is AppResult.Error -> Unit
            }
        }

        return when (remoteResult) {
            is AppResult.Success -> AppResult.Success(
                remoteResult.data + mapOf("local_due_occurrences" to localDue),
            )
            is AppResult.Error -> remoteResult
        }
    }

    private suspend fun ensureRunningKernel() {
        registerComponentsIfNeeded()
        when (runtimeKernel.kernelState) {
            RuntimeKernelState.CREATED -> {
                runtimeKernel.initialize()
                runtimeKernel.recover()
                runtimeKernel.start()
            }
            RuntimeKernelState.INITIALIZING -> {
                runtimeKernel.recover()
                runtimeKernel.start()
            }
            RuntimeKernelState.RUNNING -> Unit
            RuntimeKernelState.STOPPED -> {
                runtimeKernel.initialize()
                runtimeKernel.recover()
                runtimeKernel.start()
            }
            RuntimeKernelState.FAILED -> throw IllegalRuntimeTransitionException(
                "Kernel is FAILED until process restart",
            )
            else -> Unit
        }
    }
}
