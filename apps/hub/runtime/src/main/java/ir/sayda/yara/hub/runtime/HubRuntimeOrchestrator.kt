package ir.sayda.yara.hub.runtime

import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.IllegalRuntimeTransitionException
import ir.sayda.yara.hub.core.runtime.RuntimeKernel
import ir.sayda.yara.hub.core.runtime.RuntimeKernelState
import ir.sayda.yara.hub.runtime.component.CommunicationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.DeviceReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.IntegrationRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SchedulingReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SynchronizationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.WorkflowReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.scheduling.SchedulingReplicaRuntime
import ir.sayda.yara.hub.runtime.workflow.WorkflowReplicaRuntime
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HubRuntimeOrchestrator @Inject constructor(
    private val runtimeKernel: RuntimeKernel,
    private val schedulingReplicaRuntime: SchedulingReplicaRuntime,
    private val workflowReplicaRuntime: WorkflowReplicaRuntime,
    private val schedulingRuntime: SchedulingReplicaRuntimeComponent,
    private val workflowRuntime: WorkflowReplicaRuntimeComponent,
    private val synchronizationRuntime: SynchronizationReplicaRuntimeComponent,
    private val deviceRuntime: DeviceReplicaRuntimeComponent,
    private val communicationRuntime: CommunicationReplicaRuntimeComponent,
    private val integrationRuntime: IntegrationRuntimeComponent,
    private val runtimeAlarmCoordinator: RuntimeAlarmCoordinator,
    private val provisioningGate: RuntimeProvisioningGate,
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

    suspend fun recoverKernel(): AppResult<Unit> {
        if (!provisioningGate.requireRuntimeReady()) {
            return AppResult.Success(Unit)
        }
        return try {
            registerComponentsIfNeeded()
            runtimeKernel.restoreFromPersistence()
            ensureRunningKernel()
            AppResult.Success(Unit)
        } catch (exception: IllegalRuntimeTransitionException) {
            AppResult.Error(exception)
        }
    }

    suspend fun reconcileReplicaRuntime(): AppResult<Unit> {
        if (!provisioningGate.requireRuntimeReady()) {
            return AppResult.Success(Unit)
        }
        return try {
            ensureRunningKernel()
            runtimeAlarmCoordinator.syncAlarmsFromReplicas()
            workflowReplicaRuntime.dispatchActiveReminders()
            AppResult.Success(Unit)
        } catch (exception: IllegalRuntimeTransitionException) {
            AppResult.Error(exception)
        }
    }

    suspend fun recover(): AppResult<Unit> {
        when (val kernel = recoverKernel()) {
            is AppResult.Error -> return kernel
            is AppResult.Success -> Unit
        }
        return reconcileReplicaRuntime()
    }

    suspend fun runCycle(): AppResult<Map<String, Int>> {
        if (!provisioningGate.requireRuntimeReady()) {
            return AppResult.Success(emptyMap())
        }
        try {
            ensureRunningKernel()
        } catch (exception: IllegalRuntimeTransitionException) {
            return AppResult.Error(exception)
        }

        val now = System.currentTimeMillis()
        val schedulingResult = schedulingReplicaRuntime.hydrateAndEvaluate(now)
        val workflowResult = workflowReplicaRuntime.processDueOccurrences(now)
        val remindersDispatched = workflowReplicaRuntime.dispatchActiveReminders()

        return AppResult.Success(
            mapOf(
                "schedules_observed" to schedulingResult.schedulesObserved,
                "occurrences_generated" to schedulingResult.occurrencesGenerated,
                "occurrences_marked_due" to schedulingResult.occurrencesMarkedDue,
                "executions_started" to workflowResult.executionsStarted,
                "reminders_dispatched" to remindersDispatched,
            ),
        )
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
