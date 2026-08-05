package ir.sayda.yara.hub.runtime.workflow

import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.RuntimeDispatcher
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.workflow.WorkflowExecutionStatus
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.identity.computeExecutionId
import ir.sayda.yara.hub.runtime.support.InMemoryCareRepository
import ir.sayda.yara.hub.runtime.support.InMemorySchedulingRepository
import ir.sayda.yara.hub.runtime.support.InMemoryWorkflowRepository
import ir.sayda.yara.hub.runtime.support.sampleCareActivity
import ir.sayda.yara.hub.runtime.support.sampleDueOccurrence
import ir.sayda.yara.hub.runtime.support.sampleWorkflowDefinition
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class WorkflowReplicaRuntimeTest {

    @Test
    fun startsExecutionForDueOccurrence() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        workflowRepository.seedDefinition(sampleWorkflowDefinition())
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())
        val events = mutableListOf<RuntimeEvent>()
        val eventBus = object : ir.sayda.yara.hub.core.runtime.RuntimeEventBus {
            override suspend fun publish(event: RuntimeEvent) {
                events += event
            }
            override fun observe() = kotlinx.coroutines.flow.emptyFlow<RuntimeEvent>()
        }
        val runtime = WorkflowReplicaRuntime(
            schedulingRepository = schedulingRepository,
            workflowRepository = workflowRepository,
            careRepository = careRepository,
            runtimeDispatcher = NoOpDispatcher,
            eventBus = eventBus,
        )

        val result = runtime.processDueOccurrences(now)

        assertEquals(1, result.executionsStarted)
        val execution = workflowRepository.allExecutions().single()
        assertEquals(computeExecutionId(occurrence.id), execution.id)
        assertEquals(WorkflowExecutionStatus.ACTIVE.name, execution.status)
        assertTrue(events.any { it is RuntimeEvent.ExecutionStarted })
    }

    @Test
    fun dispatchesShowReminderForActiveExecution() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        workflowRepository.seedDefinition(sampleWorkflowDefinition())
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())
        val recordingDispatcher = RecordingDispatcher()
        val runtime = WorkflowReplicaRuntime(
            schedulingRepository = schedulingRepository,
            workflowRepository = workflowRepository,
            careRepository = careRepository,
            runtimeDispatcher = recordingDispatcher,
            eventBus = RuntimeEventBusImpl(),
        )
        runtime.processDueOccurrences(now)

        val dispatched = runtime.dispatchActiveReminders()

        assertEquals(1, dispatched)
        assertEquals("SHOW_REMINDER", recordingDispatcher.lastActionType)
    }

    private object NoOpDispatcher : RuntimeDispatcher {
        override suspend fun dispatch(
            actionType: String,
            actionPayload: String,
            executionId: String,
        ): AppDispatchResult = AppDispatchResult(true, "noop", "ok")
    }

    private class RecordingDispatcher : RuntimeDispatcher {
        var lastActionType: String? = null
        override suspend fun dispatch(
            actionType: String,
            actionPayload: String,
            executionId: String,
        ): AppDispatchResult {
            lastActionType = actionType
            return AppDispatchResult(true, "reminder_ui", "ok")
        }
    }
}
