package ir.sayda.yara.hub.runtime.usecase

import ir.sayda.yara.hub.core.workflow.WorkflowExecutionStatus
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.support.InMemoryCareRepository
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

class ConfirmReminderUseCaseImplTest {

    @Test
    fun queuesPendingEvidenceWithoutMutatingExecutionReplica() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        workflowRepository.seedDefinition(sampleWorkflowDefinition())
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())
        val pendingEvidenceRepository = InMemoryPendingEvidenceRepository()
        val eventBus = RuntimeEventBusImpl()
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
            eventBus = eventBus,
        )
        workflowRuntime.processDueOccurrences(now)
        val executionId = workflowRepository.allExecutions().single().id
        val useCase = ConfirmReminderUseCaseImpl(
            pendingEvidenceRepository = pendingEvidenceRepository,
            workflowReplicaRepository = workflowRepository,
            eventBus = eventBus,
        )

        val result = useCase.invoke(executionId, interactionReference = "confirm-button")

        assertTrue(result is ir.sayda.yara.hub.core.result.AppResult.Success)
        val evidence = pendingEvidenceRepository.queued.single()
        assertEquals("HUB_CONFIRMATION", evidence.evidenceType)
        assertEquals("PENDING", evidence.status)
        assertEquals(executionId, evidence.workflowExecutionId)
        assertEquals(WorkflowExecutionStatus.ACTIVE.name, workflowRepository.getExecution(executionId)?.status)
    }

    @Test
    fun returnsExistingEvidenceWithoutDuplicateEnqueue() = runTest {
        val now = 1_700_000_000_000L
        val occurrence = sampleDueOccurrence(scheduledForEpochMillis = now - 1_000L)
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedOccurrence(occurrence)
        val workflowRepository = InMemoryWorkflowRepository()
        workflowRepository.seedDefinition(sampleWorkflowDefinition())
        val careRepository = InMemoryCareRepository()
        careRepository.seedActivity(sampleCareActivity())
        val pendingEvidenceRepository = InMemoryPendingEvidenceRepository()
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
        val useCase = ConfirmReminderUseCaseImpl(
            pendingEvidenceRepository = pendingEvidenceRepository,
            workflowReplicaRepository = workflowRepository,
            eventBus = RuntimeEventBusImpl(),
        )

        val first = useCase.invoke(executionId, interactionReference = "confirm-button")
        val second = useCase.invoke(executionId, interactionReference = "confirm-button")

        assertTrue(first is ir.sayda.yara.hub.core.result.AppResult.Success)
        assertTrue(second is ir.sayda.yara.hub.core.result.AppResult.Success)
        assertEquals(1, pendingEvidenceRepository.queued.size)
        assertEquals(
            (first as ir.sayda.yara.hub.core.result.AppResult.Success).data,
            (second as ir.sayda.yara.hub.core.result.AppResult.Success).data,
        )
    }
}
