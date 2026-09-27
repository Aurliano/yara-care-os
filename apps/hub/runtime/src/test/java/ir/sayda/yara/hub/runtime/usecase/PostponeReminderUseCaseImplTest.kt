package ir.sayda.yara.hub.runtime.usecase

import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.core.workflow.WorkflowExecutionStatus
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.support.InMemoryCareRepository
import ir.sayda.yara.hub.runtime.support.InMemoryOccurrenceAlarmRegistry
import ir.sayda.yara.hub.runtime.support.InMemoryPendingEvidenceRepository
import ir.sayda.yara.hub.runtime.support.InMemorySchedulingRepository
import ir.sayda.yara.hub.runtime.support.InMemoryWorkflowRepository
import ir.sayda.yara.hub.runtime.support.sampleCareActivity
import ir.sayda.yara.hub.runtime.support.sampleDueOccurrence
import ir.sayda.yara.hub.runtime.support.sampleWorkflowDefinition
import ir.sayda.yara.hub.runtime.workflow.WorkflowReplicaRuntime
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PostponeReminderUseCaseImplTest {

    private val noOpScheduler = object : RuntimeScheduler {
        override fun schedulePeriodicRuntimeWork() = Unit
        override fun scheduleOneTimeRuntimeWork(occurrenceId: String?) = Unit
        override fun scheduleDelayedRuntimeWork(occurrenceId: String, delayMs: Long) = Unit
        override fun scheduleRecurringSyncPoll(delayMs: Long) = Unit
    }

    @Test
    fun postponeDoesNotMutateOccurrenceScheduledForAndEnqueuesEvidence() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val originalScheduledFor = occurrence.scheduledForEpochMillis

        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        val definition = sampleWorkflowDefinition().copy(
            definitionJson = """
                {
                  "step_timeout_seconds": 900,
                  "initial_action": {"type": "SHOW_REMINDER"},
                  "postpone": {"allowed": true, "max_count": 2, "delay_seconds": 300}
                }
            """.trimIndent(),
        )
        workflowRepository.seedDefinition(definition)
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())
        val pendingEvidenceRepository = InMemoryPendingEvidenceRepository()
        val alarmCoordinator = RuntimeAlarmCoordinator(schedulingRepository, InMemoryOccurrenceAlarmRegistry())
        val workflowRuntime = WorkflowReplicaRuntime(
            schedulingRepository = schedulingRepository,
            workflowRepository = workflowRepository,
            careRepository = careRepository,
            runtimeDispatcher = object : ir.sayda.yara.hub.core.runtime.RuntimeDispatcher {
                override suspend fun dispatch(
                    actionType: String,
                    actionPayload: String,
                    executionId: String,
                ) = ir.sayda.yara.hub.core.runtime.AppDispatchResult(true, "noop", "ok")
            },
            eventBus = RuntimeEventBusImpl(),
        )
        workflowRuntime.processDueOccurrences(now)
        val executionId = workflowRepository.allExecutions().single().id

        val useCase = PostponeReminderUseCaseImpl(
            workflowReplicaRepository = workflowRepository,
            schedulingReplicaRepository = schedulingRepository,
            careReplicaRepository = careRepository,
            pendingEvidenceRepository = pendingEvidenceRepository,
            runtimeAlarmCoordinator = alarmCoordinator,
            runtimeScheduler = noOpScheduler,
            workflowReplicaRuntime = workflowRuntime,
        )

        val result = useCase.invoke(executionId, interactionReference = "postpone-ref-1")
        assertTrue(result is AppResult.Success)

        // Invariant: Occurrence.scheduled_for MUST NOT be mutated!
        val savedOccurrence = schedulingRepository.getOccurrence(occurrence.id)!!
        assertEquals(originalScheduledFor, savedOccurrence.scheduledForEpochMillis)

        // Invariant: WorkflowExecution postpone count incremented
        val savedExecution = workflowRepository.getExecution(executionId)!!
        assertEquals(1, savedExecution.postponeCount)

        // Durable evidence was queued
        val queued = pendingEvidenceRepository.getPending()
        assertEquals(1, queued.size)
        assertEquals("POSTPONE", queued.single().evidenceType)
        assertEquals("postpone-ref-1", queued.single().interactionReference)

        // Idempotent retry with same interaction reference
        val retryResult = useCase.invoke(executionId, interactionReference = "postpone-ref-1")
        assertTrue(retryResult is AppResult.Success)
        assertEquals(1, pendingEvidenceRepository.getPending().size)
        assertEquals(1, workflowRepository.getExecution(executionId)!!.postponeCount)

        // Second postpone with different reference
        val secondResult = useCase.invoke(executionId, interactionReference = "postpone-ref-2")
        assertTrue(secondResult is AppResult.Success)
        assertEquals(2, workflowRepository.getExecution(executionId)!!.postponeCount)

        // Third postpone exceeds max count 2
        val thirdResult = useCase.invoke(executionId, interactionReference = "postpone-ref-3")
        assertTrue(thirdResult is AppResult.Error)
    }
}
