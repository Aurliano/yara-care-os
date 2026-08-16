package ir.sayda.yara.hub.runtime.dispatcher

import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.RuntimeActionHandler
import ir.sayda.yara.hub.runtime.communication.CommunicationRuntime
import ir.sayda.yara.hub.runtime.json.HubJsonReader
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InitiateCallActionHandler @Inject constructor(
    private val communicationRuntime: CommunicationRuntime,
    private val authRepository: AuthRepository,
) : RuntimeActionHandler {
    override val actionType: String = "INITIATE_CALL"
    override val targetComponentId: String = "communication_replica_runtime"

    override suspend fun handle(actionPayload: String, executionId: String): AppDispatchResult {
        return try {
            val recipientContactId = HubJsonReader.requireString(actionPayload, "recipient_contact_id")
            val channel = HubJsonReader.optString(actionPayload, "channel", DEFAULT_CHANNEL).ifBlank { DEFAULT_CHANNEL }
            val payloadElderId = HubJsonReader.optString(actionPayload, "elder_id")
            val elderId = payloadElderId.ifBlank { authRepository.getIdentity()?.elderId.orEmpty() }
            if (elderId.isBlank()) {
                return AppDispatchResult(
                    accepted = false,
                    routedTo = targetComponentId,
                    message = "elder_id is required to start a call",
                )
            }
            when (val started = communicationRuntime.startCall(elderId, channel, recipientContactId)) {
                is AppResult.Success -> AppDispatchResult(
                    accepted = true,
                    routedTo = targetComponentId,
                    message = "Call session ${started.data.sessionId}",
                )
                is AppResult.Error -> AppDispatchResult(
                    accepted = false,
                    routedTo = targetComponentId,
                    message = started.message,
                )
            }
        } catch (exception: Exception) {
            AppDispatchResult(
                accepted = false,
                routedTo = targetComponentId,
                message = exception.message.orEmpty(),
            )
        }
    }

    private companion object {
        const val DEFAULT_CHANNEL = "VOICE"
    }
}
