package ir.sayda.yara.hub.runtime.bootstrap

import ir.sayda.yara.hub.core.domain.model.WorkflowDefinition
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.first

/**
 * Ensures workflow definitions referenced by local care activities exist on the hub replica.
 * Backend snapshot/delta may stage care activities before workflow definitions on some sync paths.
 */
@Singleton
class HubWorkflowBootstrap @Inject constructor(
    private val workflowRepository: WorkflowReplicaRepository,
    private val careRepository: CareReplicaRepository,
) {
    suspend fun ensureWorkflowDefinitionsForCareActivities(): Int {
        val activities = careRepository.observeAllCareActivities().first()
        val now = System.currentTimeMillis()
        var created = 0
        activities
            .map { it.workflowDefinitionId }
            .distinct()
            .filter { it.isNotBlank() }
            .forEach { definitionId ->
                if (workflowRepository.getDefinition(definitionId) != null) return@forEach
                workflowRepository.upsertDefinition(
                    WorkflowDefinition(
                        id = definitionId,
                        code = "hub-local-bootstrap",
                        name = "Medication Reminder",
                        status = "ACTIVE",
                        definitionJson = DEFAULT_DEFINITION_JSON,
                        updatedAtEpochMillis = now,
                    ),
                )
                created++
            }
        return created
    }

    companion object {
        private val DEFAULT_DEFINITION_JSON = """
            {
              "initial_action": {"type": "SHOW_REMINDER"},
              "confirmation_policy": {"accepted_evidence_types": ["HUB_CONFIRMATION"]},
              "step_timeout_seconds": 900,
              "retry": {"max_retries": 2, "action": {"type": "SHOW_REMINDER"}, "timeout_seconds": 900},
              "postpone": {"allowed": true, "max_count": 2, "delay_seconds": 300},
              "escalation_steps": [{"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": 900}]
            }
        """.trimIndent()
    }
}
