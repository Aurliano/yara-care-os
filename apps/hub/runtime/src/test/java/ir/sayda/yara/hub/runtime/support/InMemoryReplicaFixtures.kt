package ir.sayda.yara.hub.runtime.support

import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.PendingEvidence
import ir.sayda.yara.hub.core.domain.model.Prescription
import ir.sayda.yara.hub.core.domain.model.ScheduleDefinition
import ir.sayda.yara.hub.core.domain.model.WorkflowDefinition
import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.model.SyncSession
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.SyncSessionLocalRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.core.scheduling.ScheduleStatus
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import java.util.UUID

class InMemorySchedulingRepository : SchedulingReplicaRepository {
    private val schedules = MutableStateFlow<List<ScheduleDefinition>>(emptyList())
    private val occurrences = MutableStateFlow<List<Occurrence>>(emptyList())

    override val replicaType: String = "scheduling"

    override fun observeScheduleDefinitions(): Flow<List<ScheduleDefinition>> = schedules.asStateFlow()

    override fun observeOccurrences(): Flow<List<Occurrence>> = occurrences.asStateFlow()

    override fun observeOccurrencesDueBefore(epochMillis: Long): Flow<List<Occurrence>> =
        occurrences.asStateFlow().map { list ->
            list.filter {
                it.scheduledForEpochMillis <= epochMillis &&
                    it.status == OccurrenceStatus.DUE.name
            }
        }

    override fun observeTodayReminders(endOfDayEpochMillis: Long): Flow<List<Occurrence>> =
        occurrences.asStateFlow().map { list ->
            list.filter {
                it.scheduledForEpochMillis <= endOfDayEpochMillis &&
                    (it.status == OccurrenceStatus.DUE.name || it.status == OccurrenceStatus.SCHEDULED.name)
            }.sortedBy { it.scheduledForEpochMillis }
        }

    override suspend fun getOccurrence(occurrenceId: String): Occurrence? =
        occurrences.value.firstOrNull { it.id == occurrenceId }

    override suspend fun upsertScheduleDefinition(schedule: ScheduleDefinition) {
        schedules.value = schedules.value.filterNot { it.id == schedule.id } + schedule
    }

    override suspend fun upsertOccurrence(occurrence: Occurrence) {
        occurrences.value = occurrences.value.filterNot { it.id == occurrence.id } + occurrence
    }

    override suspend fun getOccurrencesDueBefore(epochMillis: Long): List<Occurrence> =
        occurrences.value.filter {
            it.scheduledForEpochMillis <= epochMillis &&
                it.status == OccurrenceStatus.DUE.name
        }

    override suspend fun getScheduledOccurrencesDueBefore(epochMillis: Long): List<Occurrence> =
        occurrences.value.filter {
            it.scheduledForEpochMillis <= epochMillis &&
                it.status == OccurrenceStatus.SCHEDULED.name
        }

    override suspend fun getScheduledOccurrencesAfter(epochMillis: Long): List<Occurrence> =
        occurrences.value.filter {
            it.scheduledForEpochMillis > epochMillis &&
                it.status == OccurrenceStatus.SCHEDULED.name
        }

    override suspend fun replaceOccurrencesForSchedule(
        scheduleDefinitionId: String,
        occurrences: List<Occurrence>,
    ) {
        this.occurrences.value = this.occurrences.value
            .filterNot { it.scheduleDefinitionId == scheduleDefinitionId } + occurrences
    }

    override fun observeNextScheduledOccurrence(afterEpochMillis: Long): Flow<Occurrence?> =
        occurrences.asStateFlow().map { list ->
            list.filter {
                it.scheduledForEpochMillis > afterEpochMillis &&
                    it.status == OccurrenceStatus.SCHEDULED.name
            }.minByOrNull { it.scheduledForEpochMillis }
        }

    override fun observeNextReminderOccurrence(
        nowEpochMillis: Long,
        endOfDayEpochMillis: Long,
    ): Flow<Occurrence?> =
        occurrences.asStateFlow().map { list ->
            list.filter { occurrence ->
                (occurrence.status == OccurrenceStatus.DUE.name &&
                    occurrence.scheduledForEpochMillis <= endOfDayEpochMillis) ||
                    (occurrence.status == OccurrenceStatus.SCHEDULED.name &&
                        occurrence.scheduledForEpochMillis > nowEpochMillis)
            }.minByOrNull { it.scheduledForEpochMillis }
        }

    fun seedSchedule(schedule: ScheduleDefinition) {
        schedules.value = listOf(schedule)
    }

    fun seedOccurrence(occurrence: Occurrence) {
        occurrences.value = listOf(occurrence)
    }

    fun allOccurrences(): List<Occurrence> = occurrences.value
}

class InMemoryWorkflowRepository : WorkflowReplicaRepository {
    private val definitions = MutableStateFlow<List<WorkflowDefinition>>(emptyList())
    private val executions = MutableStateFlow<List<WorkflowExecution>>(emptyList())

    override val replicaType: String = "workflow"

    override fun observeActiveExecutions(): Flow<List<WorkflowExecution>> =
        executions.asStateFlow().map { list -> list.filter { it.status == "ACTIVE" } }

    override fun observeDefinitions(): Flow<List<WorkflowDefinition>> = definitions.asStateFlow()

    override suspend fun getDefinition(definitionId: String): WorkflowDefinition? =
        definitions.value.firstOrNull { it.id == definitionId }

    override suspend fun getExecutionByOccurrence(occurrenceId: String): WorkflowExecution? =
        executions.value.firstOrNull { it.occurrenceId == occurrenceId }

    override suspend fun upsertExecution(execution: WorkflowExecution) {
        executions.value = executions.value.filterNot { it.id == execution.id } + execution
    }

    override suspend fun getExecution(executionId: String): WorkflowExecution? =
        executions.value.firstOrNull { it.id == executionId }

    override suspend fun upsertDefinition(definition: WorkflowDefinition) {
        definitions.value = definitions.value.filterNot { it.id == definition.id } + definition
    }

    fun seedDefinition(definition: WorkflowDefinition) {
        definitions.value = listOf(definition)
    }

    fun allExecutions(): List<WorkflowExecution> = executions.value
}

class InMemoryCareRepository : CareReplicaRepository {
    private val activities = MutableStateFlow<List<CareActivity>>(emptyList())
    private val prescriptions = MutableStateFlow<List<Prescription>>(emptyList())

    override val replicaType: String = "care"

    override fun observeActiveCareActivities(elderId: String): Flow<List<CareActivity>> =
        MutableStateFlow(activities.value.filter { it.elderId == elderId }).asStateFlow()

    override fun observeAllCareActivities(): Flow<List<CareActivity>> = activities.asStateFlow()

    override suspend fun getCareActivityByScheduleDefinition(scheduleDefinitionId: String): CareActivity? =
        activities.value.firstOrNull { it.scheduleDefinitionId == scheduleDefinitionId }

    override suspend fun upsertCareActivity(activity: CareActivity) {
        activities.value = activities.value.filterNot { it.id == activity.id } + activity
    }

    override fun observePrescriptions(): Flow<List<Prescription>> = prescriptions.asStateFlow()

    override suspend fun getPrescription(careActivityId: String): Prescription? =
        prescriptions.value.firstOrNull { it.careActivityId == careActivityId }

    override suspend fun upsertPrescription(prescription: Prescription) {
        prescriptions.value = prescriptions.value.filterNot { it.careActivityId == prescription.careActivityId } +
            prescription
    }

    fun seedActivity(activity: CareActivity) {
        activities.value = listOf(activity)
    }
}

class InMemoryPendingEvidenceRepository : PendingEvidenceRepository {
    val queued = mutableListOf<PendingEvidence>()

    override suspend fun enqueue(
        workflowExecutionId: String,
        evidenceType: String,
        interactionReference: String,
        payloadJson: String,
        correlationId: String,
        idempotencyKey: String,
    ): PendingEvidence {
        val evidence = PendingEvidence(
            id = UUID.randomUUID().toString(),
            workflowExecutionId = workflowExecutionId,
            evidenceType = evidenceType,
            interactionReference = interactionReference,
            payloadJson = payloadJson,
            correlationId = correlationId,
            idempotencyKey = idempotencyKey,
            status = "PENDING",
            retryCount = 0,
            createdAtEpochMillis = System.currentTimeMillis(),
            updatedAtEpochMillis = System.currentTimeMillis(),
            lastAttemptAtEpochMillis = null,
            lastError = null,
        )
        queued += evidence
        return evidence
    }

    override suspend fun findHubConfirmationEvidence(workflowExecutionId: String): PendingEvidence? =
        queued.lastOrNull { it.workflowExecutionId == workflowExecutionId && it.evidenceType == "HUB_CONFIRMATION" }

    override fun observeHubConfirmationEvidence(): Flow<List<PendingEvidence>> =
        MutableStateFlow(queued.filter { it.evidenceType == "HUB_CONFIRMATION" }).asStateFlow()

    override fun observePendingCount(): Flow<Int> =
        MutableStateFlow(queued.count { it.status == "PENDING" }).asStateFlow()

    override suspend fun getPending(limit: Int): List<PendingEvidence> =
        queued.filter { it.status == "PENDING" }.take(limit)

    override suspend fun markSubmitted(id: String) {
        queued.replaceAll { if (it.id == id) it.copy(status = "SUBMITTED") else it }
    }

    override suspend fun markInFlight(id: String) {
        queued.replaceAll { if (it.id == id) it.copy(status = "IN_FLIGHT") else it }
    }

    override suspend fun revertToPending(id: String) {
        queued.replaceAll { if (it.id == id) it.copy(status = "PENDING") else it }
    }

    override suspend fun markFailed(id: String, incrementRetry: Boolean, lastError: String?) {
        queued.replaceAll {
            if (it.id == id) {
                it.copy(
                    status = "FAILED",
                    retryCount = if (incrementRetry) it.retryCount + 1 else it.retryCount,
                    lastError = lastError,
                )
            } else {
                it
            }
        }
    }
}

object NoOpSyncSessionLocalRepository : SyncSessionLocalRepository {
    override suspend fun save(session: SyncSession) = Unit
    override suspend fun getActive(): SyncSession? = null
    override suspend fun getById(sessionId: String): SyncSession? = null
    override suspend fun updateStatus(sessionId: String, status: String) = Unit
    override suspend fun clear(sessionId: String) = Unit
}

fun sampleSchedule(
    id: String = "schedule-1",
    startAtEpochMillis: Long,
): ScheduleDefinition = ScheduleDefinition(
    id = id,
    ownerReference = "care-activity-1",
    recurrenceDefinitionJson = """{"type":"once"}""",
    timezone = "UTC",
    startAtEpochMillis = startAtEpochMillis,
    endAtEpochMillis = null,
    status = ScheduleStatus.ACTIVE.name,
    updatedAtEpochMillis = startAtEpochMillis,
)

fun sampleCareActivity(
    scheduleDefinitionId: String = "schedule-1",
    workflowDefinitionId: String = "workflow-def-1",
): CareActivity = CareActivity(
    id = "care-activity-1",
    elderId = "elder-1",
    activityType = "MEDICATION",
    status = "ACTIVE",
    scheduleDefinitionId = scheduleDefinitionId,
    workflowDefinitionId = workflowDefinitionId,
    displayTitle = "آسپرین",
    displaySubtitle = "یک قرص",
    displayIcon = "pill",
    confirmationRequirementJson = "{}",
    compartmentAssignmentReference = "",
    aggregateVersion = 1,
    updatedAtEpochMillis = System.currentTimeMillis(),
)

fun sampleWorkflowDefinition(
    id: String = "workflow-def-1",
): WorkflowDefinition = WorkflowDefinition(
    id = id,
    code = "medication_reminder",
    name = "Medication Reminder",
    status = "ACTIVE",
    definitionJson = """
        {
          "step_timeout_seconds": 3600,
          "initial_action": {
            "type": "SHOW_REMINDER",
            "title": "یادآور دارو"
          }
        }
    """.trimIndent(),
    updatedAtEpochMillis = System.currentTimeMillis(),
)

fun sampleDueOccurrence(
    id: String = "occ-1",
    scheduleDefinitionId: String = "schedule-1",
    scheduledForEpochMillis: Long,
): Occurrence = Occurrence(
    id = id,
    scheduleDefinitionId = scheduleDefinitionId,
    scheduledForEpochMillis = scheduledForEpochMillis,
    status = OccurrenceStatus.DUE.name,
    updatedAtEpochMillis = scheduledForEpochMillis,
)
