package ir.sayda.yara.hub.runtime

import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.RuntimeComponent
import ir.sayda.yara.hub.core.runtime.RuntimeHealth
import ir.sayda.yara.hub.core.runtime.RuntimeKernel
import ir.sayda.yara.hub.core.runtime.RuntimeKernelState
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.component.CommunicationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.DeviceReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.IntegrationRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SchedulingReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SynchronizationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.WorkflowReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.dispatcher.ActionDispatcher
import ir.sayda.yara.hub.runtime.dispatcher.DefaultActionRegistry
import ir.sayda.yara.hub.runtime.dispatcher.ShowReminderActionHandler
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.scheduling.SchedulingReplicaRuntime
import ir.sayda.yara.hub.runtime.support.AlwaysAllowedProvisioningGate
import ir.sayda.yara.hub.runtime.support.DeniedProvisioningGate
import ir.sayda.yara.hub.runtime.support.InMemoryCareRepository
import ir.sayda.yara.hub.runtime.support.InMemoryOccurrenceAlarmRegistry
import ir.sayda.yara.hub.runtime.support.InMemorySchedulingRepository
import ir.sayda.yara.hub.runtime.support.NoOpSyncSessionLocalRepository
import ir.sayda.yara.hub.runtime.support.InMemoryWorkflowRepository
import ir.sayda.yara.hub.runtime.support.sampleCareActivity
import ir.sayda.yara.hub.runtime.support.sampleDueOccurrence
import ir.sayda.yara.hub.runtime.support.sampleSchedule
import ir.sayda.yara.hub.runtime.support.sampleWorkflowDefinition
import ir.sayda.yara.hub.runtime.workflow.WorkflowReplicaRuntime
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertTrue
import org.junit.Test

class HubRuntimeOrchestratorRecoveryTest {

    @Test
    fun recoverRestoresKernelStateAndAlarms() = runTest {
        val schedulingRepository = InMemorySchedulingRepository()
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val alarmCoordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val kernel = RecordingRuntimeKernel(initialState = RuntimeKernelState.STOPPED)
        val now = System.currentTimeMillis()
        schedulingRepository.upsertOccurrence(
            Occurrence(
                id = "occ-future",
                scheduleDefinitionId = "schedule-1",
                scheduledForEpochMillis = now + 120_000L,
                status = OccurrenceStatus.SCHEDULED.name,
                updatedAtEpochMillis = now,
            ),
        )
        val orchestrator = OrchestratorTestSupport.buildOrchestrator(
            kernel = kernel,
            schedulingRepository = schedulingRepository,
            alarmCoordinator = alarmCoordinator,
        )

        val result = orchestrator.recover()

        assertTrue(result is AppResult.Success)
        assertTrue(kernel.restoreFromPersistenceCalled)
        assertTrue(kernel.initializeCalled)
        assertTrue(alarmRegistry.isOccurrenceAlarmRegistered("occ-future"))
    }

    @Test
    fun recoverSkipsKernelWhenProvisioningGateClosed() = runTest {
        val schedulingRepository = InMemorySchedulingRepository()
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val alarmCoordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val kernel = RecordingRuntimeKernel(initialState = RuntimeKernelState.STOPPED)
        val orchestrator = OrchestratorTestSupport.buildOrchestrator(
            kernel = kernel,
            schedulingRepository = schedulingRepository,
            alarmCoordinator = alarmCoordinator,
            provisioningGate = DeniedProvisioningGate(),
        )

        val result = orchestrator.recover()

        assertTrue(result is AppResult.Success)
        assertTrue(!kernel.restoreFromPersistenceCalled)
        assertTrue(!kernel.initializeCalled)
    }

    private fun buildOrchestrator(
        kernel: RuntimeKernel,
        schedulingRepository: InMemorySchedulingRepository,
        alarmCoordinator: RuntimeAlarmCoordinator,
    ): HubRuntimeOrchestrator = OrchestratorTestSupport.buildOrchestrator(
        kernel,
        schedulingRepository,
        alarmCoordinator,
    )

    private class RecordingRuntimeKernel(
        initialState: RuntimeKernelState,
    ) : RuntimeKernel {
        var restoreFromPersistenceCalled = false
        var initializeCalled = false
        override var kernelState: RuntimeKernelState = initialState
            private set

        override fun register(component: RuntimeComponent) = Unit
        override fun unregister(componentId: String) = Unit
        override suspend fun initialize() {
            initializeCalled = true
            kernelState = RuntimeKernelState.INITIALIZING
        }
        override suspend fun recover() {
            kernelState = RuntimeKernelState.RUNNING
        }
        override suspend fun start() = Unit
        override suspend fun stop() = Unit
        override suspend fun restoreFromPersistence() {
            restoreFromPersistenceCalled = true
            kernelState = RuntimeKernelState.CREATED
        }
        override suspend fun health(): RuntimeHealth =
            RuntimeHealth(healthy = true, state = kernelState.name)
        override fun componentHealth(componentId: String): RuntimeHealth? = null
        override fun allComponentHealth(): Map<String, RuntimeHealth> = emptyMap()
    }
}

class ReminderWakeFlowTest {

    @Test
    fun runCycleOpensReminderThroughRuntimePath() = runTest {
        val now = 1_700_000_000_000L
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedSchedule(sampleSchedule(startAtEpochMillis = now - 60_000L))
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val alarmCoordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val workflowRepository = InMemoryWorkflowRepository()
        workflowRepository.seedDefinition(sampleWorkflowDefinition())
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())
        val gateway = RecordingGateway()
        val dispatcher = ActionDispatcher(
            DefaultActionRegistry(
                setOf(
                    ShowReminderActionHandler(
                        reminderPresentationGateway = gateway,
                        reminderNotificationGateway = NoOpNotificationGateway(),
                        eventBus = RuntimeEventBusImpl(),
                    ),
                ),
            ),
        )
        val workflowReplicaRuntime = WorkflowReplicaRuntime(
            schedulingRepository = schedulingRepository,
            workflowRepository = workflowRepository,
            careRepository = careRepository,
            runtimeDispatcher = dispatcher,
            eventBus = RuntimeEventBusImpl(),
        )
        val kernel = RecordingRuntimeKernel(RuntimeKernelState.RUNNING)
        val orchestrator = HubRuntimeOrchestrator(
            runtimeKernel = kernel,
            schedulingReplicaRuntime = SchedulingReplicaRuntime(
                schedulingRepository,
                RuntimeEventBusImpl(),
                alarmCoordinator,
            ),
            workflowReplicaRuntime = workflowReplicaRuntime,
            schedulingRuntime = SchedulingReplicaRuntimeComponent(),
            workflowRuntime = WorkflowReplicaRuntimeComponent(),
            synchronizationRuntime = SynchronizationReplicaRuntimeComponent(NoOpSyncSessionLocalRepository),
            deviceRuntime = DeviceReplicaRuntimeComponent(),
            communicationRuntime = CommunicationReplicaRuntimeComponent(),
            integrationRuntime = IntegrationRuntimeComponent(),
            runtimeAlarmCoordinator = alarmCoordinator,
            provisioningGate = AlwaysAllowedProvisioningGate(),
            hubWorkflowBootstrap = ir.sayda.yara.hub.runtime.bootstrap.HubWorkflowBootstrap(
                workflowRepository,
                careRepository,
            ),
        )

        val result = orchestrator.runCycle()

        assertTrue(result is AppResult.Success)
        assertTrue(gateway.opened)
    }

    private class RecordingGateway : ir.sayda.yara.hub.core.runtime.ReminderPresentationGateway {
        var opened = false
        override suspend fun openReminder(executionId: String, occurrenceId: String) {
            opened = true
        }
        override fun observeOpenRequests(): Flow<ir.sayda.yara.hub.core.runtime.ReminderOpenRequest> =
            MutableSharedFlow()
    }

    private class NoOpNotificationGateway : ir.sayda.yara.hub.core.runtime.ReminderNotificationGateway {
        override suspend fun showReminderNotification(executionId: String, occurrenceId: String) = Unit
        override fun cancelReminderNotification(executionId: String) = Unit
    }

    private class RecordingRuntimeKernel(
        initialState: RuntimeKernelState,
    ) : RuntimeKernel {
        override var kernelState: RuntimeKernelState = initialState
            private set
        override fun register(component: RuntimeComponent) = Unit
        override fun unregister(componentId: String) = Unit
        override suspend fun initialize() {
            kernelState = RuntimeKernelState.INITIALIZING
        }
        override suspend fun recover() {
            kernelState = RuntimeKernelState.RUNNING
        }
        override suspend fun start() = Unit
        override suspend fun stop() = Unit
        override suspend fun restoreFromPersistence() = Unit
        override suspend fun health(): RuntimeHealth =
            RuntimeHealth(healthy = true, state = kernelState.name)
        override fun componentHealth(componentId: String): RuntimeHealth? = null
        override fun allComponentHealth(): Map<String, RuntimeHealth> = emptyMap()
    }
}

class BootRecoveryFlowTest {

    @Test
    fun recoverRuntimeUseCaseRestoresAlarmsWithoutBusinessChanges() = runTest {
        val now = System.currentTimeMillis()
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.upsertOccurrence(
            sampleDueOccurrence(
                id = "occ-due",
                scheduledForEpochMillis = now - 1_000L,
            ).copy(status = OccurrenceStatus.SCHEDULED.name),
        )
        schedulingRepository.upsertOccurrence(
            Occurrence(
                id = "occ-future",
                scheduleDefinitionId = "schedule-1",
                scheduledForEpochMillis = now + 300_000L,
                status = OccurrenceStatus.SCHEDULED.name,
                updatedAtEpochMillis = now,
            ),
        )
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val alarmCoordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val kernel = RecordingRuntimeKernel(RuntimeKernelState.STOPPED)
        val orchestrator = OrchestratorTestSupport.buildOrchestrator(
            kernel = kernel,
            schedulingRepository = schedulingRepository,
            alarmCoordinator = alarmCoordinator,
        )
        val recoverUseCase = ir.sayda.yara.hub.runtime.usecase.RecoverRuntimeUseCaseImpl(orchestrator)
        val reconcileUseCase = ir.sayda.yara.hub.runtime.usecase.ReconcileRuntimeUseCaseImpl(orchestrator)

        recoverUseCase()
        val result = reconcileUseCase()

        assertTrue(result is AppResult.Success)
        assertTrue(alarmRegistry.isOccurrenceAlarmRegistered("occ-future"))
        assertTrue(!alarmRegistry.isOccurrenceAlarmRegistered("occ-due"))
    }

    private class RecordingRuntimeKernel(
        initialState: RuntimeKernelState,
    ) : RuntimeKernel {
        override var kernelState: RuntimeKernelState = initialState
            private set
        override fun register(component: RuntimeComponent) = Unit
        override fun unregister(componentId: String) = Unit
        override suspend fun initialize() {
            kernelState = RuntimeKernelState.INITIALIZING
        }
        override suspend fun recover() {
            kernelState = RuntimeKernelState.RUNNING
        }
        override suspend fun start() = Unit
        override suspend fun stop() = Unit
        override suspend fun restoreFromPersistence() {
            kernelState = RuntimeKernelState.CREATED
        }
        override suspend fun health(): RuntimeHealth =
            RuntimeHealth(healthy = true, state = kernelState.name)
        override fun componentHealth(componentId: String): RuntimeHealth? = null
        override fun allComponentHealth(): Map<String, RuntimeHealth> = emptyMap()
    }
}
