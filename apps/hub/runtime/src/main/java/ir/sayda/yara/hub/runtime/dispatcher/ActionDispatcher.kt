package ir.sayda.yara.hub.runtime.dispatcher

import ir.sayda.yara.hub.core.runtime.ActionRegistry
import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.RuntimeActionHandler
import ir.sayda.yara.hub.core.runtime.RuntimeDispatcher
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DefaultActionRegistry @Inject constructor(
    handlers: Set<@JvmSuppressWildcards RuntimeActionHandler>,
) : ActionRegistry {

    private val handlersByType = handlers.associateBy { it.actionType }

    override fun handlerFor(actionType: String): RuntimeActionHandler? = handlersByType[actionType]

    override fun registeredActionTypes(): Set<String> = handlersByType.keys
}

@Singleton
class ActionDispatcher @Inject constructor(
    private val actionRegistry: ActionRegistry,
) : RuntimeDispatcher {

    override suspend fun dispatch(
        actionType: String,
        actionPayload: String,
        executionId: String,
    ): AppDispatchResult {
        val handler = actionRegistry.handlerFor(actionType)
            ?: return AppDispatchResult(
                accepted = false,
                routedTo = "",
                message = "Unsupported action type: $actionType",
            )
        return handler.handle(actionPayload, executionId)
    }
}
