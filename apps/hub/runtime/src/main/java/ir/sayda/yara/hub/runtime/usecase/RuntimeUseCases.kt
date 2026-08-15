package ir.sayda.yara.hub.runtime.usecase

import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.domain.usecase.ConfirmReminderUseCase
import ir.sayda.yara.hub.core.domain.usecase.PostponeReminderUseCase
import ir.sayda.yara.hub.core.domain.usecase.ReconcileRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.debug.DebugTrace
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.ReminderConfirmed
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.core.workflow.WorkflowExecutionStatus
import ir.sayda.yara.hub.runtime.HubRuntimeOrchestrator
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.workflow.WorkflowDefinitionParser
import ir.sayda.yara.hub.runtime.workflow.WorkflowReplicaRuntime
import java.util.UUID
import javax.inject.Inject

class RunIntegrationCycleUseCaseImpl @Inject constructor(
    private val orchestrator: HubRuntimeOrchestrator,
) : RunIntegrationCycleUseCase {
    override suspend fun invoke(): AppResult<Map<String, Int>> = orchestrator.runCycle()
}

class RecoverRuntimeUseCaseImpl @Inject constructor(
    private val orchestrator: HubRuntimeOrchestrator,
) : RecoverRuntimeUseCase {
    override suspend fun invoke(): AppResult<Unit> = orchestrator.recoverKernel()
}

class ReconcileRuntimeUseCaseImpl @Inject constructor(
    private val orchestrator: HubRuntimeOrchestrator,
) : ReconcileRuntimeUseCase {
    override suspend fun invoke(): AppResult<Unit> = orchestrator.reconcileReplicaRuntime()
}

class ConfirmReminderUseCaseImpl @Inject constructor(
    private val pendingEvidenceRepository: PendingEvidenceRepository,
    private val workflowReplicaRepository: WorkflowReplicaRepository,
    private val eventBus: RuntimeEventBus,
) : ConfirmReminderUseCase {

    override suspend fun invoke(executionId: String, interactionReference: String): AppResult<String> {
        val execution = workflowReplicaRepository.getExecution(executionId)
            ?: return AppResult.Error(IllegalStateException("Execution not found: $executionId"))
        if (execution.status != WorkflowExecutionStatus.ACTIVE.name) {
            return AppResult.Error(
                IllegalStateException("Execution is not active: ${execution.status}"),
            )
        }

        pendingEvidenceRepository.findHubConfirmationEvidence(executionId)?.let { existing ->
            return AppResult.Success(existing.id)
        }

        val correlationId = UUID.randomUUID().toString()
        val idempotencyKey = "confirmation:$executionId:$interactionReference"
        val evidence = pendingEvidenceRepository.enqueue(
            workflowExecutionId = execution.id,
            evidenceType = "HUB_CONFIRMATION",
            interactionReference = interactionReference,
            payloadJson = """{"execution_id":"$executionId","interaction_reference":"$interactionReference"}""",
            correlationId = correlationId,
            idempotencyKey = idempotencyKey,
        )
        eventBus.publish(
            RuntimeEvent.ReminderAcknowledged(
                ReminderConfirmed(
                    executionId = executionId,
                    occurrenceId = execution.occurrenceId,
                    pendingEvidenceId = evidence.id,
                ),
            ),
        )
        DebugTrace.log(
            "REMINDER",
            "RuntimeUseCases.kt:confirm",
            "reminder confirmed",
            mapOf("executionId" to executionId, "occurrenceId" to execution.occurrenceId),
        )
        return AppResult.Success(evidence.id)
    }
}

class PostponeReminderUseCaseImpl @Inject constructor(
    private val workflowReplicaRepository: WorkflowReplicaRepository,
    private val schedulingReplicaRepository: SchedulingReplicaRepository,
    private val careReplicaRepository: CareReplicaRepository,
    private val runtimeAlarmCoordinator: RuntimeAlarmCoordinator,
    private val runtimeScheduler: RuntimeScheduler,
    private val workflowReplicaRuntime: WorkflowReplicaRuntime,
) : PostponeReminderUseCase {

    override suspend fun invoke(executionId: String, interactionReference: String): AppResult<Long> {
        val now = System.currentTimeMillis()
        val execution = workflowReplicaRepository.getExecution(executionId)
            ?: return AppResult.Error(IllegalStateException("Execution not found: $executionId"))
        if (execution.status != WorkflowExecutionStatus.ACTIVE.name) {
            return AppResult.Error(IllegalStateException("Execution is not active: ${execution.status}"))
        }

        val occurrence = schedulingReplicaRepository.getOccurrence(execution.occurrenceId)
            ?: return AppResult.Error(IllegalStateException("Occurrence not found: ${execution.occurrenceId}"))
        val careActivity = careReplicaRepository.getCareActivityByScheduleDefinition(occurrence.scheduleDefinitionId)
            ?: return AppResult.Error(IllegalStateException("Care activity not found"))
        val definition = workflowReplicaRepository.getDefinition(careActivity.workflowDefinitionId)
            ?: return AppResult.Error(IllegalStateException("Workflow definition not found"))

        val policy = WorkflowDefinitionParser.postponePolicy(definition.definitionJson)
        if (!policy.allowed) {
            return AppResult.Error(IllegalStateException("Postpone is not allowed"))
        }
        if (execution.postponeCount >= policy.maxCount) {
            return AppResult.Error(IllegalStateException("Postpone limit reached"))
        }
        if (policy.delaySeconds <= 0L) {
            return AppResult.Error(IllegalStateException("Invalid postpone delay"))
        }

        val postponedUntil = now + policy.delaySeconds * 1000
        val timeoutSeconds = WorkflowDefinitionParser.stepTimeoutSeconds(definition.definitionJson)

        schedulingReplicaRepository.upsertOccurrence(
            occurrence.copy(
                status = OccurrenceStatus.SCHEDULED.name,
                scheduledForEpochMillis = postponedUntil,
                updatedAtEpochMillis = now,
            ),
        )
        workflowReplicaRepository.upsertExecution(
            execution.copy(
                postponeCount = execution.postponeCount + 1,
                activeUntilEpochMillis = postponedUntil + timeoutSeconds * 1000,
                updatedAtEpochMillis = now,
                aggregateVersion = execution.aggregateVersion + 1,
            ),
        )

        runtimeAlarmCoordinator.cancelAlarmForOccurrence(occurrence.id)
        runtimeAlarmCoordinator.registerAlarmForOccurrence(
            occurrenceId = occurrence.id,
            triggerAtEpochMillis = postponedUntil,
            nowEpochMillis = now,
        )
        workflowReplicaRuntime.releaseReminderDispatch(executionId)
        runtimeScheduler.scheduleDelayedRuntimeWork(
            occurrenceId = occurrence.id,
            delayMs = policy.delaySeconds * 1000,
        )

        DebugTrace.log(
            "REMINDER",
            "RuntimeUseCases.kt:postpone",
            "reminder postponed",
            mapOf(
                "executionId" to executionId,
                "occurrenceId" to occurrence.id,
                "interactionReference" to interactionReference,
                "postponedUntil" to postponedUntil,
                "postponeCount" to (execution.postponeCount + 1),
            ),
        )
        return AppResult.Success(postponedUntil)
    }
}
