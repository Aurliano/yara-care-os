package ir.sayda.yara.hub.runtime.dispatcher

import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.ReminderNotificationGateway
import ir.sayda.yara.hub.core.runtime.ReminderPresentationGateway
import ir.sayda.yara.hub.core.runtime.RuntimeActionHandler
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import ir.sayda.yara.hub.core.runtime.ReminderShown
import ir.sayda.yara.hub.runtime.json.HubJsonReader
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ShowReminderActionHandler @Inject constructor(
    private val reminderPresentationGateway: ReminderPresentationGateway,
    private val reminderNotificationGateway: ReminderNotificationGateway,
    private val eventBus: RuntimeEventBus,
) : RuntimeActionHandler {
    override val actionType: String = "SHOW_REMINDER"
    override val targetComponentId: String = "reminder_ui"

    override suspend fun handle(actionPayload: String, executionId: String): AppDispatchResult {
        val resolvedExecutionId = HubJsonReader.optString(actionPayload, "execution_id", executionId)
        val occurrenceId = HubJsonReader.requireString(actionPayload, "occurrence_id")
        reminderPresentationGateway.openReminder(resolvedExecutionId, occurrenceId)
        reminderNotificationGateway.showReminderNotification(resolvedExecutionId, occurrenceId)
        eventBus.publish(
            RuntimeEvent.ReminderDisplayed(
                ReminderShown(
                    executionId = resolvedExecutionId,
                    occurrenceId = occurrenceId,
                ),
            ),
        )
        return AppDispatchResult(
            accepted = true,
            routedTo = targetComponentId,
            message = "Reminder opened",
        )
    }
}
