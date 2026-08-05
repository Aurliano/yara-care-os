package ir.sayda.yara.hub.presentation

import ir.sayda.yara.hub.core.runtime.ReminderOpenRequest
import ir.sayda.yara.hub.core.runtime.ReminderPresentationGateway
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ReminderPresentationGatewayImpl @Inject constructor() : ReminderPresentationGateway {

    private val requests = MutableSharedFlow<ReminderOpenRequest>(extraBufferCapacity = 8)

    override suspend fun openReminder(executionId: String, occurrenceId: String) {
        requests.emit(ReminderOpenRequest(executionId = executionId, occurrenceId = occurrenceId))
    }

    override fun observeOpenRequests(): Flow<ReminderOpenRequest> = requests.asSharedFlow()
}
