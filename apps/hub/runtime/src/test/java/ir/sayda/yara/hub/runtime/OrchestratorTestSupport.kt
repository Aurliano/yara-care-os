package ir.sayda.yara.hub.runtime

import ir.sayda.yara.hub.core.runtime.RuntimeKernel
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.component.CommunicationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.DeviceReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.IntegrationRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SchedulingReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SynchronizationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.WorkflowReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.dispatcher.ActionDispatcher
import ir.sayda.yara.hub.runtime.dispatcher.DefaultActionRegistry
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.scheduling.SchedulingReplicaRuntime
import ir.sayda.yara.hub.runtime.support.InMemoryCareRepository
import ir.sayda.yara.hub.runtime.support.NoOpSyncSessionLocalRepository
import ir.sayda.yara.hub.runtime.support.InMemorySchedulingRepository
import ir.sayda.yara.hub.runtime.support.InMemoryWorkflowRepository
import ir.sayda.yara.hub.runtime.support.sampleCareActivity
import ir.sayda.yara.hub.runtime.support.sampleWorkflowDefinition
import ir.sayda.yara.hub.runtime.workflow.WorkflowReplicaRuntime

internal object OrchestratorTestSupport {
    fun buildOrchestrator(
        kernel: RuntimeKernel,
        schedulingRepository: InMemorySchedulingRepository,
        alarmCoordinator: RuntimeAlarmCoordinator,
    ): HubRuntimeOrchestrator {
        val workflowRepository = InMemoryWorkflowRepository()
        workflowRepository.seedDefinition(sampleWorkflowDefinition())
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())
        val workflowReplicaRuntime = WorkflowReplicaRuntime(
            schedulingRepository = schedulingRepository,
            workflowRepository = workflowRepository,
            careRepository = careRepository,
            runtimeDispatcher = ActionDispatcher(DefaultActionRegistry(emptySet())),
            eventBus = RuntimeEventBusImpl(),
        )
        return HubRuntimeOrchestrator(
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
        )
    }
}
