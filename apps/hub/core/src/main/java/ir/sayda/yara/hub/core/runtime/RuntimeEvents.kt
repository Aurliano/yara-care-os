package ir.sayda.yara.hub.core.runtime

data class RuntimeOccurrenceDue(
    val occurrenceId: String,
    val scheduleDefinitionId: String,
    val scheduledForEpochMillis: Long,
)

data class WorkflowStarted(
    val executionId: String,
    val occurrenceId: String,
    val workflowDefinitionId: String,
)

data class ReminderShown(
    val executionId: String,
    val occurrenceId: String,
)

data class ReminderConfirmed(
    val executionId: String,
    val occurrenceId: String,
    val pendingEvidenceId: String,
)

sealed class RuntimeEvent {
    data class OccurrenceDue(val payload: RuntimeOccurrenceDue) : RuntimeEvent()
    data class ExecutionStarted(val payload: WorkflowStarted) : RuntimeEvent()
    data class ReminderDisplayed(val payload: ReminderShown) : RuntimeEvent()
    data class ReminderAcknowledged(val payload: ReminderConfirmed) : RuntimeEvent()
}

interface RuntimeEventBus {
    suspend fun publish(event: RuntimeEvent)
    fun observe(): kotlinx.coroutines.flow.Flow<RuntimeEvent>
}

interface ReminderPresentationGateway {
    suspend fun openReminder(executionId: String, occurrenceId: String)
    fun observeOpenRequests(): kotlinx.coroutines.flow.Flow<ReminderOpenRequest>
}

data class ReminderOpenRequest(
    val executionId: String,
    val occurrenceId: String,
)

interface CommunicationPresentationGateway {
    suspend fun onCallSession(session: ir.sayda.yara.hub.core.domain.model.CallSession)
    fun observeCallSessions(): kotlinx.coroutines.flow.Flow<ir.sayda.yara.hub.core.domain.model.CallSession>
}
