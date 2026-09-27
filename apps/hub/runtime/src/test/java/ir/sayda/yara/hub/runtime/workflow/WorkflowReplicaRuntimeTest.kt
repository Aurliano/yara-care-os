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
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
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

    @Test
    fun doesNotStartExecutionWhenCareActivityIsPausedOrEnded() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        workflowRepository.seedDefinition(sampleWorkflowDefinition())
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity().copy(status = "PAUSED"))
        val runtime = WorkflowReplicaRuntime(
            schedulingRepository = schedulingRepository,
            workflowRepository = workflowRepository,
            careRepository = careRepository,
            runtimeDispatcher = NoOpDispatcher,
            eventBus = RuntimeEventBusImpl(),
        )

        val result = runtime.processDueOccurrences(now)

        assertEquals(0, result.executionsStarted)
        assertTrue(workflowRepository.allExecutions().isEmpty())
    }

    @Test
    fun offlineTimeoutsProgressThroughRetriesEscalationAndMissed() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        val definitionWithPolicy = sampleWorkflowDefinition().copy(
            definitionJson = """
                {
                  "step_timeout_seconds": 900,
                  "initial_action": {"type": "SHOW_REMINDER"},
                  "retry": {"max_retries": 2, "timeout_seconds": 900},
                  "escalation_steps": [{"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": 900}]
                }
            """.trimIndent(),
        )
        workflowRepository.seedDefinition(definitionWithPolicy)
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
        val execution = workflowRepository.allExecutions().single()
        assertEquals(0, execution.retryCount)

        // Timeout 1: Retry 1
        var processed = runtime.processTimeouts(now + 900_001L)
        assertEquals(1, processed)
        var updated = workflowRepository.getExecution(execution.id)!!
        assertEquals(1, updated.retryCount)
        assertEquals("ACTIVE", updated.status)

        // Timeout 2: Retry 2
        processed = runtime.processTimeouts(now + 1_800_002L)
        assertEquals(1, processed)
        updated = workflowRepository.getExecution(execution.id)!!
        assertEquals(2, updated.retryCount)
        assertEquals(0, updated.escalationIndex)
        assertEquals("ACTIVE", updated.status)

        // Timeout 3: Escalation 1
        processed = runtime.processTimeouts(now + 2_700_003L)
        assertEquals(1, processed)
        updated = workflowRepository.getExecution(execution.id)!!
        assertEquals(1, updated.escalationIndex)
        assertEquals("NOTIFY_CAREGIVER", recordingDispatcher.lastActionType)
        assertEquals("ACTIVE", updated.status)

        // Timeout 4: Final timeout -> MISSED
        processed = runtime.processTimeouts(now + 3_600_004L)
        assertEquals(1, processed)
        updated = workflowRepository.getExecution(execution.id)!!
        assertEquals(WorkflowExecutionStatus.MISSED.name, updated.status)
        assertTrue(updated.completedAtEpochMillis != null)
    }

    @Test
    fun processTimeoutsUnderConcurrentInvocationsPerformsExactlyOneTransition() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        val definitionWithPolicy = sampleWorkflowDefinition().copy(
            definitionJson = """
                {
                  "step_timeout_seconds": 900,
                  "initial_action": {"type": "SHOW_REMINDER"},
                  "retry": {"max_retries": 2, "timeout_seconds": 900},
                  "escalation_steps": [{"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": 900}]
                }
            """.trimIndent(),
        )
        workflowRepository.seedDefinition(definitionWithPolicy)
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())

        val runtime = WorkflowReplicaRuntime(
            schedulingRepository = schedulingRepository,
            workflowRepository = workflowRepository,
            careRepository = careRepository,
            runtimeDispatcher = NoOpDispatcher,
            eventBus = RuntimeEventBusImpl(),
        )

        runtime.processDueOccurrences(now)
        val execution = workflowRepository.allExecutions().single()
        assertEquals(0, execution.retryCount)

        // Invoke processTimeouts concurrently from multiple workers at the exact same timeout boundary
        val timeoutBoundary = now + 900_005L
        val deferred1 = async { runtime.processTimeouts(timeoutBoundary) }
        val deferred2 = async { runtime.processTimeouts(timeoutBoundary) }
        val deferred3 = async { runtime.processTimeouts(timeoutBoundary) }

        val results = awaitAll(deferred1, deferred2, deferred3)
        // Exactly one worker processed the transition (sum == 1)
        assertEquals(1, results.sum())

        val updated = workflowRepository.getExecution(execution.id)!!
        // retryCount incremented exactly once: 0 -> 1, not 0 -> 2 or 3
        assertEquals(1, updated.retryCount)
        assertEquals("ACTIVE", updated.status)
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
