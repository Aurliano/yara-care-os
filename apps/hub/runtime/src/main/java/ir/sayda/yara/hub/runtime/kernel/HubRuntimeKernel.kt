package ir.sayda.yara.hub.runtime.kernel

import ir.sayda.yara.hub.core.runtime.RUNTIME_KERNEL_COMPONENT_ID
import ir.sayda.yara.hub.core.domain.model.RuntimeStateRecord
import ir.sayda.yara.hub.core.domain.repository.RuntimeStateRepository
import ir.sayda.yara.hub.core.runtime.IllegalRuntimeTransitionException
import ir.sayda.yara.hub.core.runtime.RuntimeComponent
import ir.sayda.yara.hub.core.runtime.RuntimeHealth
import ir.sayda.yara.hub.core.runtime.RuntimeKernel
import ir.sayda.yara.hub.core.runtime.RuntimeKernelState
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HubRuntimeKernel @Inject constructor(
    private val runtimeStateRepository: RuntimeStateRepository,
) : RuntimeKernel {

    private val components = linkedMapOf<String, RuntimeComponent>()
    private val componentHealthCache = linkedMapOf<String, RuntimeHealth>()
    private var state: RuntimeKernelState = RuntimeKernelState.CREATED

    override val kernelState: RuntimeKernelState get() = state

    override fun register(component: RuntimeComponent) {
        if (state == RuntimeKernelState.FAILED) {
            throw IllegalRuntimeTransitionException("Cannot register components while kernel is FAILED")
        }
        components[component.componentId] = component
    }

    override fun unregister(componentId: String) {
        components.remove(componentId)
        componentHealthCache.remove(componentId)
    }

    override suspend fun initialize() {
        if (state == RuntimeKernelState.STOPPED) {
            state = RuntimeKernelState.CREATED
        }
        transition(RuntimeKernelState.CREATED, RuntimeKernelState.INITIALIZING)
        components.values.forEach { component ->
            component.initialize()
            cacheComponentHealth(component)
        }
        persistKernelState(RuntimeKernelState.INITIALIZING)
    }

    override suspend fun recover() {
        transition(RuntimeKernelState.INITIALIZING, RuntimeKernelState.RECOVERING)
        components.values.forEach { component ->
            component.recover()
            cacheComponentHealth(component)
        }
        transition(RuntimeKernelState.RECOVERING, RuntimeKernelState.RUNNING)
        persistKernelState(RuntimeKernelState.RUNNING)
    }

    override suspend fun start() {
        requireState(RuntimeKernelState.RUNNING)
        components.values.forEach { component ->
            component.start()
            cacheComponentHealth(component)
        }
        persistKernelState(RuntimeKernelState.RUNNING)
    }

    override suspend fun stop() {
        if (state == RuntimeKernelState.STOPPED || state == RuntimeKernelState.FAILED) {
            return
        }
        transition(RuntimeKernelState.RUNNING, RuntimeKernelState.STOPPING)
        components.values.forEach { component ->
            component.stop()
            cacheComponentHealth(component)
        }
        transition(RuntimeKernelState.STOPPING, RuntimeKernelState.STOPPED)
        persistKernelState(RuntimeKernelState.STOPPED)
    }

    override suspend fun health(): RuntimeHealth {
        val componentHealth = allComponentHealth()
        val unhealthy = componentHealth.values.any { !it.healthy }
        return RuntimeHealth(
            healthy = state == RuntimeKernelState.RUNNING && !unhealthy,
            state = state.name,
            detail = if (unhealthy) "One or more runtime components are unhealthy" else "Kernel is ${state.name}",
        )
    }

    override fun componentHealth(componentId: String): RuntimeHealth? = componentHealthCache[componentId]

    override fun allComponentHealth(): Map<String, RuntimeHealth> = componentHealthCache.toMap()

    suspend fun markFailed(reason: String) {
        state = RuntimeKernelState.FAILED
        persistKernelState(RuntimeKernelState.FAILED, reason)
    }

    suspend fun restoreFromPersistence() {
        val persisted = runtimeStateRepository.get(RUNTIME_KERNEL_COMPONENT_ID) ?: return
        state = runCatching { RuntimeKernelState.valueOf(persisted.lifecycleState) }
            .getOrDefault(RuntimeKernelState.CREATED)
        if (state == RuntimeKernelState.FAILED) {
            throw IllegalRuntimeTransitionException(
                "Kernel is FAILED until process restart: ${persisted.statePayloadJson}",
            )
        }
    }

    private suspend fun cacheComponentHealth(component: RuntimeComponent) {
        componentHealthCache[component.componentId] = component.health()
    }

    private fun transition(from: RuntimeKernelState, to: RuntimeKernelState) {
        if (state != from) {
            throw IllegalRuntimeTransitionException("Illegal kernel transition: $state → $to (expected from $from)")
        }
        state = to
    }

    private fun requireState(expected: RuntimeKernelState) {
        if (state != expected) {
            throw IllegalRuntimeTransitionException("Kernel must be $expected but was $state")
        }
    }

    private suspend fun persistKernelState(
        kernelState: RuntimeKernelState,
        detail: String = "",
    ) {
        runtimeStateRepository.upsert(
            RuntimeStateRecord(
                componentId = RUNTIME_KERNEL_COMPONENT_ID,
                lifecycleState = kernelState.name,
                statePayloadJson = if (detail.isBlank()) "{}" else """{"detail":"$detail"}""",
                updatedAtEpochMillis = System.currentTimeMillis(),
            ),
        )
        components.keys.forEach { componentId ->
            val health = componentHealthCache[componentId]
            runtimeStateRepository.upsert(
                RuntimeStateRecord(
                    componentId = componentId,
                    lifecycleState = health?.state ?: kernelState.name,
                    statePayloadJson = """{"healthy":${health?.healthy ?: true}}""",
                    updatedAtEpochMillis = System.currentTimeMillis(),
                ),
            )
        }
    }

    companion object {
        const val KERNEL_COMPONENT_ID = RUNTIME_KERNEL_COMPONENT_ID
    }
}
