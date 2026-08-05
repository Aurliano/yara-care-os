package ir.sayda.yara.hub.runtime.dispatcher

import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.RuntimeActionHandler
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeferredDeviceActionHandler @Inject constructor() : RuntimeActionHandler {
    override val actionType: String = "OPEN_COMPARTMENT"
    override val targetComponentId: String = "device_replica_runtime"

    override suspend fun handle(actionPayload: String, executionId: String): AppDispatchResult =
        AppDispatchResult(
            accepted = true,
            routedTo = targetComponentId,
            message = "Deferred to Sprint II-C",
        )
}

@Singleton
class DeferredCommunicationActionHandler @Inject constructor() : RuntimeActionHandler {
    override val actionType: String = "INITIATE_CALL"
    override val targetComponentId: String = "communication_replica_runtime"

    override suspend fun handle(actionPayload: String, executionId: String): AppDispatchResult =
        AppDispatchResult(
            accepted = true,
            routedTo = targetComponentId,
            message = "Deferred to Sprint II-D",
        )
}
