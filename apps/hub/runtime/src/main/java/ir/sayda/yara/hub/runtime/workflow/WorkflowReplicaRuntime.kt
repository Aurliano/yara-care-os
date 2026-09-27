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
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
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
    private val timeoutMutex = Mutex()

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
        if (careActivity == null || careActivity.status != "ACTIVE") return null
        val definition = workflowRepository.getDefinition(careActivity.workflowDefinitionId)
        if (definition == null) return null
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

    suspend fun processTimeouts(nowEpochMillis: Long = System.currentTimeMillis()): Int = timeoutMutex.withLock {
        val activeExecutions = workflowRepository.observeActiveExecutions().first()
        var processed = 0
        for (item in activeExecutions) {
            val execution = workflowRepository.getExecution(item.id) ?: continue
            if (execution.status != WorkflowExecutionStatus.ACTIVE.name) continue
            val activeUntil = execution.activeUntilEpochMillis ?: continue
            if (activeUntil > nowEpochMillis) continue

            val definition = workflowRepository.getDefinition(execution.workflowDefinitionId) ?: continue
            val definitionJson = definition.definitionJson
            val timeoutSeconds = WorkflowDefinitionParser.stepTimeoutSeconds(definitionJson)

            val retryPolicy = WorkflowDefinitionParser.retryPolicy(definitionJson)
            if (retryPolicy.allowed && execution.retryCount < retryPolicy.maxRetries) {
                val nextRetry = execution.retryCount + 1
                val retryTimeout = if (retryPolicy.timeoutSeconds > 0) retryPolicy.timeoutSeconds else timeoutSeconds
                workflowRepository.upsertExecution(
                    execution.copy(
                        retryCount = nextRetry,
                        currentStep = "retry_$nextRetry",
                        activeUntilEpochMillis = nowEpochMillis + (retryTimeout * 1000),
                        updatedAtEpochMillis = nowEpochMillis,
                    ),
                )
                releaseReminderDispatch(execution.id)
                processed++
                continue
            }

            val escalationSteps = WorkflowDefinitionParser.escalationSteps(definitionJson)
            if (execution.escalationIndex < escalationSteps.size) {
                val nextIndex = execution.escalationIndex + 1
                val step = escalationSteps[nextIndex - 1]
                val escalationTimeout = if (step.timeoutSeconds > 0) step.timeoutSeconds else timeoutSeconds
                workflowRepository.upsertExecution(
                    execution.copy(
                        escalationIndex = nextIndex,
                        currentStep = "escalation_$nextIndex",
                        currentActionJson = step.actionJson,
                        activeUntilEpochMillis = nowEpochMillis + (escalationTimeout * 1000),
                        updatedAtEpochMillis = nowEpochMillis,
                    ),
                )
                runtimeDispatcher.dispatch(
                    actionType = step.actionType,
                    actionPayload = HubJsonReader.buildObject(
                        "execution_id" to execution.id,
                        "occurrence_id" to execution.occurrenceId,
                    ),
                    executionId = execution.id,
                )
                processed++
                continue
            }

            workflowRepository.upsertExecution(
                execution.copy(
                    status = WorkflowExecutionStatus.MISSED.name,
                    completedAtEpochMillis = nowEpochMillis,
                    updatedAtEpochMillis = nowEpochMillis,
                ),
            )
            releaseReminderDispatch(execution.id)
            processed++
        }
        return@withLock processed
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
