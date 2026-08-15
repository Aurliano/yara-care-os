package ir.sayda.yara.hub.runtime.workflow

import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.RuntimeDispatcher
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import ir.sayda.yara.hub.core.runtime.WorkflowStarted
import kotlinx.coroutines.flow.first
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.core.workflow.WorkflowActionType
import ir.sayda.yara.hub.core.workflow.WorkflowExecutionStatus
import ir.sayda.yara.hub.runtime.identity.computeExecutionId
import ir.sayda.yara.hub.runtime.json.HubJsonReader
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WorkflowReplicaRuntime @Inject constructor(
    private val schedulingRepository: SchedulingReplicaRepository,
    private val workflowRepository: WorkflowReplicaRepository,
    private val careRepository: CareReplicaRepository,
    private val runtimeDispatcher: RuntimeDispatcher,
    private val eventBus: RuntimeEventBus,
) {
    private val dispatchedExecutionIds = mutableSetOf<String>()

    suspend fun processDueOccurrences(nowEpochMillis: Long = System.currentTimeMillis()): WorkflowCycleResult {
        val dueOccurrences = schedulingRepository.getOccurrencesDueBefore(nowEpochMillis)
        var started = 0
        for (occurrence in dueOccurrences) {
            if (occurrence.status != OccurrenceStatus.DUE.name) continue
            val execution = startExecutionForOccurrence(occurrence, nowEpochMillis)
            if (execution != null) started++
        }
        return WorkflowCycleResult(executionsStarted = started)
    }

    suspend fun dispatchActiveReminders(): Int {
        val executions = workflowRepository.observeActiveExecutions().first()
        var dispatched = 0
        executions.forEach { execution ->
            if (dispatchReminderIfNeeded(execution)) dispatched++
        }
        return dispatched
    }

    fun releaseReminderDispatch(executionId: String) {
        dispatchedExecutionIds.remove(executionId)
    }

    private suspend fun startExecutionForOccurrence(
        occurrence: ir.sayda.yara.hub.core.domain.model.Occurrence,
        nowEpochMillis: Long,
    ): WorkflowExecution? {
        val careActivity = careRepository.getCareActivityByScheduleDefinition(occurrence.scheduleDefinitionId)
        val definition = careActivity?.let { workflowRepository.getDefinition(it.workflowDefinitionId) }
        if (careActivity == null || definition == null) return null
        val executionId = computeExecutionId(occurrence.id)
        val existing = workflowRepository.getExecution(executionId)
        if (existing != null && existing.status in TERMINAL_OR_ACTIVE) {
            return existing
        }

        val timeoutSeconds = WorkflowDefinitionParser.stepTimeoutSeconds(definition.definitionJson)
        val actionJson = WorkflowDefinitionParser.initialActionJson(definition.definitionJson)
        val execution = WorkflowExecution(
            id = executionId,
            occurrenceId = occurrence.id,
            workflowDefinitionId = definition.id,
            status = WorkflowExecutionStatus.ACTIVE.name,
            currentStep = "initial",
            postponeCount = 0,
            retryCount = 0,
            escalationIndex = 0,
            currentActionJson = actionJson,
            activeUntilEpochMillis = nowEpochMillis + (timeoutSeconds * 1000),
            startedAtEpochMillis = nowEpochMillis,
            completedAtEpochMillis = null,
            aggregateVersion = 1,
            updatedAtEpochMillis = nowEpochMillis,
        )
        workflowRepository.upsertExecution(execution)
        eventBus.publish(
            RuntimeEvent.ExecutionStarted(
                WorkflowStarted(
                    executionId = execution.id,
                    occurrenceId = occurrence.id,
                    workflowDefinitionId = definition.id,
                ),
            ),
        )
        return execution
    }

    private suspend fun dispatchReminderIfNeeded(execution: WorkflowExecution): Boolean {
        val actionType = runCatching {
            HubJsonReader.requireString(execution.currentActionJson, "type")
        }.getOrNull()
        if (execution.id in dispatchedExecutionIds) return false
        if (execution.status != WorkflowExecutionStatus.ACTIVE.name) return false
        if (actionType == null) return false
        if (actionType != WorkflowActionType.SHOW_REMINDER.name) return false

        val payload = HubJsonReader.buildObject(
            "execution_id" to execution.id,
            "occurrence_id" to execution.occurrenceId,
        )
        val result = runtimeDispatcher.dispatch(
            actionType = actionType,
            actionPayload = payload,
            executionId = execution.id,
        )
        if (result.accepted) {
            dispatchedExecutionIds += execution.id
            return true
        }
        return false
    }

    companion object {
        private val TERMINAL_OR_ACTIVE = setOf(
            WorkflowExecutionStatus.ACTIVE.name,
            WorkflowExecutionStatus.CONFIRMED.name,
            WorkflowExecutionStatus.MISSED.name,
            WorkflowExecutionStatus.CANCELLED.name,
            WorkflowExecutionStatus.FAILED.name,
        )
    }
}

data class WorkflowCycleResult(
    val executionsStarted: Int,
)
