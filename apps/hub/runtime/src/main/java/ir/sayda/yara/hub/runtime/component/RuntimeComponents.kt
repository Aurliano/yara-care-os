package ir.sayda.yara.hub.runtime.component

import ir.sayda.yara.hub.core.runtime.RuntimeComponent
import ir.sayda.yara.hub.core.runtime.RuntimeHealth

abstract class BaseRuntimeComponent(
    final override val componentId: String,
) : RuntimeComponent {

    protected enum class ComponentPhase {
        CREATED,
        INITIALIZED,
        RECOVERED,
        RUNNING,
        STOPPED,
    }

    protected var phase: ComponentPhase = ComponentPhase.CREATED

    override suspend fun initialize() {
        phase = ComponentPhase.INITIALIZED
    }

    override suspend fun recover() {
        phase = ComponentPhase.RECOVERED
    }

    override suspend fun start() {
        phase = ComponentPhase.RUNNING
    }

    override suspend fun stop() {
        phase = ComponentPhase.STOPPED
    }

    override suspend fun health(): RuntimeHealth = RuntimeHealth(
        healthy = phase != ComponentPhase.STOPPED,
        state = phase.name,
        detail = componentId,
    )
}

class SchedulingReplicaRuntimeComponent : BaseRuntimeComponent("scheduling_replica_runtime")

class WorkflowReplicaRuntimeComponent : BaseRuntimeComponent("workflow_replica_runtime")

class DeviceReplicaRuntimeComponent : BaseRuntimeComponent("device_replica_runtime")

class CommunicationReplicaRuntimeComponent(
    private val communicationRuntime: ir.sayda.yara.hub.runtime.communication.CommunicationRuntime? = null,
) : BaseRuntimeComponent("communication_replica_runtime") {
    override suspend fun recover() {
        communicationRuntime?.recover()
        super.recover()
    }
}

class IntegrationRuntimeComponent : BaseRuntimeComponent("integration_runtime")
