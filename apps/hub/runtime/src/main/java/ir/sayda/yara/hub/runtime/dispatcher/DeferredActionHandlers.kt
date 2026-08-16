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
