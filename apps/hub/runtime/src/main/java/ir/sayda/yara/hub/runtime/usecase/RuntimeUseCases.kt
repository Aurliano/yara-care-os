package ir.sayda.yara.hub.runtime.usecase

import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.domain.usecase.ConfirmReminderUseCase
import ir.sayda.yara.hub.core.domain.usecase.ReconcileRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.ReminderConfirmed
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import ir.sayda.yara.hub.core.workflow.WorkflowExecutionStatus
import ir.sayda.yara.hub.runtime.HubRuntimeOrchestrator
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
        return AppResult.Success(evidence.id)
    }
}
