package ir.sayda.yara.hub.core.runtime

enum class RuntimeKernelState {
    CREATED,
    INITIALIZING,
    RECOVERING,
    RUNNING,
    STOPPING,
    STOPPED,
    FAILED,
}

data class RuntimeHealth(
    val healthy: Boolean,
    val state: String,
    val detail: String = "",
)

class IllegalRuntimeTransitionException(
    message: String,
) : IllegalStateException(message)

interface RuntimeComponent {
    val componentId: String

    suspend fun initialize()

    suspend fun recover()

    suspend fun start()

    suspend fun stop()

    suspend fun health(): RuntimeHealth
}

interface RuntimeKernel {
    val kernelState: RuntimeKernelState

    fun register(component: RuntimeComponent)

    fun unregister(componentId: String)

    suspend fun initialize()

    suspend fun recover()

    suspend fun start()

    suspend fun stop()

    suspend fun restoreFromPersistence()

    suspend fun health(): RuntimeHealth

    fun componentHealth(componentId: String): RuntimeHealth?

    fun allComponentHealth(): Map<String, RuntimeHealth>
}

interface RuntimeDispatcher {
    suspend fun dispatch(actionType: String, actionPayload: String, executionId: String): AppDispatchResult
}

data class AppDispatchResult(
    val accepted: Boolean,
    val routedTo: String,
    val message: String = "",
)

interface RuntimeActionHandler {
    val actionType: String
    val targetComponentId: String
    suspend fun handle(actionPayload: String, executionId: String): AppDispatchResult
}

interface ActionRegistry {
    fun handlerFor(actionType: String): RuntimeActionHandler?
    fun registeredActionTypes(): Set<String>
}

interface RuntimeScheduler {
    fun schedulePeriodicRuntimeWork()
    fun scheduleOneTimeRuntimeWork(occurrenceId: String? = null)
    fun scheduleDelayedRuntimeWork(occurrenceId: String, delayMs: Long)
    fun scheduleRecurringSyncPoll(delayMs: Long = 60_000L)
}

const val RUNTIME_KERNEL_COMPONENT_ID = "__kernel__"
