package ir.sayda.yara.hub.core.domain.repository

import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.CommunicationSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.Device
import ir.sayda.yara.hub.core.domain.model.DeviceCommand
import ir.sayda.yara.hub.core.domain.model.ConnectivitySnapshot
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.model.ProvisioningStatus
import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.OutboxEntry
import ir.sayda.yara.hub.core.domain.model.PendingEvidence
import ir.sayda.yara.hub.core.domain.model.Prescription
import ir.sayda.yara.hub.core.domain.model.ReminderPresentation
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.domain.model.RuntimeStateRecord
import ir.sayda.yara.hub.core.domain.model.ScheduleDefinition
import ir.sayda.yara.hub.core.domain.model.SyncSession
import ir.sayda.yara.hub.core.domain.model.WorkflowDefinition
import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.OutboxOperationType
import ir.sayda.yara.hub.core.sync.SyncDirection
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    suspend fun getIdentity(): HubIdentity?
    suspend fun saveIdentity(identity: HubIdentity)
    suspend fun clearIdentity()
    suspend fun login(phone: String, password: String): AppResult<HubIdentity>
    suspend fun logout(): AppResult<Unit>
    suspend fun refreshTokenIfNeeded(): AppResult<HubIdentity>
    suspend fun refreshToken(): AppResult<HubIdentity>
    fun observeIdentity(): Flow<HubIdentity?>
}

interface ProvisioningRepository {
    suspend fun registerDevice(serialNumber: String, deviceModelCode: String): AppResult<ProvisioningStatus>
    suspend fun authenticate(deviceId: String, phone: String, password: String): AppResult<HubIdentity>
    suspend fun restoreProvisioning(): AppResult<ProvisioningStatus>
    suspend fun revokeProvisioning(): AppResult<Unit>
    suspend fun getStatus(): ProvisioningStatus
    fun observeProvisioningStatus(): Flow<ProvisioningStatus>
    suspend fun setProvisioningState(state: ProvisioningState, errorMessage: String? = null)
}

interface ReplicaMetadataRepository {
    suspend fun getReplicaState(): ReplicaState?
    suspend fun upsertReplicaState(state: ReplicaState)
    suspend fun advanceCheckpoint(sequence: Long, token: String?)
    suspend fun touchLastSuccessfulSync()
    fun observeReplicaState(): Flow<ReplicaState?>
}

interface ReplicaRepository<T> {
    val replicaType: String
    suspend fun upsert(item: T)
}

interface CareReplicaRepository : ReplicaRepository<CareActivity> {
    override val replicaType: String get() = "care"
    fun observeActiveCareActivities(elderId: String): Flow<List<CareActivity>>
    fun observeAllCareActivities(): Flow<List<CareActivity>>
    suspend fun getCareActivityByScheduleDefinition(scheduleDefinitionId: String): CareActivity?
    suspend fun upsertCareActivity(activity: CareActivity)
    override suspend fun upsert(item: CareActivity) = upsertCareActivity(item)
    fun observePrescriptions(): Flow<List<Prescription>>
    suspend fun getPrescription(careActivityId: String): Prescription?
    suspend fun upsertPrescription(prescription: Prescription)
}

interface SchedulingReplicaRepository : ReplicaRepository<ScheduleDefinition> {
    override val replicaType: String get() = "scheduling"
    fun observeScheduleDefinitions(): Flow<List<ScheduleDefinition>>
    fun observeOccurrences(): Flow<List<Occurrence>>
    fun observeOccurrencesDueBefore(epochMillis: Long): Flow<List<Occurrence>>
    suspend fun getOccurrence(occurrenceId: String): Occurrence?
    suspend fun upsertScheduleDefinition(schedule: ScheduleDefinition)
    override suspend fun upsert(item: ScheduleDefinition) = upsertScheduleDefinition(item)
    suspend fun upsertOccurrence(occurrence: Occurrence)
    suspend fun getOccurrencesDueBefore(epochMillis: Long): List<Occurrence>
    suspend fun getScheduledOccurrencesDueBefore(epochMillis: Long): List<Occurrence>
    suspend fun getScheduledOccurrencesAfter(epochMillis: Long): List<Occurrence>
    fun observeNextScheduledOccurrence(afterEpochMillis: Long): Flow<Occurrence?>
}

interface WorkflowReplicaRepository : ReplicaRepository<WorkflowExecution> {
    override val replicaType: String get() = "workflow"
    fun observeActiveExecutions(): Flow<List<WorkflowExecution>>
    fun observeDefinitions(): Flow<List<WorkflowDefinition>>
    suspend fun getDefinition(definitionId: String): WorkflowDefinition?
    suspend fun getExecutionByOccurrence(occurrenceId: String): WorkflowExecution?
    suspend fun upsertExecution(execution: WorkflowExecution)
    override suspend fun upsert(item: WorkflowExecution) = upsertExecution(item)
    suspend fun getExecution(executionId: String): WorkflowExecution?
    suspend fun upsertDefinition(definition: WorkflowDefinition)
}

interface DeviceReplicaRepository : ReplicaRepository<Device> {
    override val replicaType: String get() = "device"
    override suspend fun upsert(item: Device) = upsertDevice(item)
    suspend fun upsertDevice(device: Device)
    suspend fun upsertCommand(command: DeviceCommand)
    suspend fun getQueuedCommands(): List<DeviceCommand>
}

interface CommunicationReplicaRepository : ReplicaRepository<Contact> {
    override val replicaType: String get() = "communication"
    override suspend fun upsert(item: Contact) = upsertContact(item)
    fun observePriorityContacts(elderId: String): Flow<List<Contact>>
    suspend fun upsertContact(contact: Contact)
    suspend fun upsertSession(session: CommunicationSession)
}

interface OutboxRepository {
    suspend fun enqueue(
        operationType: OutboxOperationType,
        payloadJson: String,
        idempotencyKey: String,
        priority: Int = 0,
    ): OutboxEntry
    suspend fun getPendingEntries(limit: Int = 50): List<OutboxEntry>
    suspend fun markInFlight(entryId: String)
    suspend fun markCompleted(entryId: String)
    suspend fun markFailed(entryId: String, incrementRetry: Boolean = true, lastError: String? = null)
}

interface PendingEvidenceRepository {
    suspend fun enqueue(
        workflowExecutionId: String,
        evidenceType: String,
        interactionReference: String,
        payloadJson: String,
        correlationId: String,
        idempotencyKey: String,
    ): PendingEvidence
    suspend fun getPending(limit: Int = 50): List<PendingEvidence>
    suspend fun findHubConfirmationEvidence(workflowExecutionId: String): PendingEvidence?
    fun observeHubConfirmationEvidence(): Flow<List<PendingEvidence>>
    fun observePendingCount(): Flow<Int>
    suspend fun markSubmitted(id: String)
    suspend fun markInFlight(id: String)
    suspend fun revertToPending(id: String)
    suspend fun markFailed(id: String, incrementRetry: Boolean = true, lastError: String? = null)
}

interface RuntimeStateRepository {
    suspend fun upsert(record: RuntimeStateRecord)
    suspend fun get(componentId: String): RuntimeStateRecord?
    suspend fun getAll(): List<RuntimeStateRecord>
    fun observeKernelState(): Flow<RuntimeStateRecord?>
}

interface SynchronizationRepository {
    suspend fun startSession(direction: SyncDirection, idempotencyKey: String): AppResult<SyncSession>
    suspend fun fetchPendingOperations(sessionId: String): AppResult<List<ir.sayda.yara.hub.core.sync.SyncOperation>>
    suspend fun resumeSession(sessionId: String): AppResult<SyncSession>
    suspend fun cancelSession(sessionId: String): AppResult<Unit>
    suspend fun fetchCheckpoint(replicaId: String): AppResult<ReplicaCheckpoint>
    suspend fun completeDownloadSession(sessionId: String): AppResult<Unit>
    suspend fun submitDelta(
        sessionId: String,
        aggregateReference: String,
        aggregateVersion: String,
        payloadJson: String,
        payloadType: String,
        payloadHash: String,
        idempotencyKey: String,
    ): AppResult<Unit>
    suspend fun submitSnapshot(
        sessionId: String,
        aggregateReference: String,
        aggregateVersion: String,
        payloadJson: String,
        payloadType: String,
        payloadHash: String,
        idempotencyKey: String,
    ): AppResult<Unit>
}

interface SyncSessionLocalRepository {
    suspend fun save(session: SyncSession)
    suspend fun getActive(): SyncSession?
    suspend fun getById(sessionId: String): SyncSession?
    suspend fun updateStatus(sessionId: String, status: String)
    suspend fun clear(sessionId: String)
}

interface SyncConflictRepository {
    suspend fun record(conflict: ir.sayda.yara.hub.core.sync.SyncConflictRecord)
    suspend fun listOpen(): List<ir.sayda.yara.hub.core.sync.SyncConflictRecord>
}

interface ReplicaSnapshotWriter {
    suspend fun replaceReplicaTables(bundle: ReplicaSnapshotBundle)
}

data class ReplicaCheckpoint(
    val replicaIdentifier: String,
    val checkpointSequence: Long,
    val checkpointToken: String?,
)

data class ReplicaSnapshotBundle(
    val careActivities: List<CareActivity> = emptyList(),
    val prescriptions: List<Prescription> = emptyList(),
    val workflowDefinitions: List<WorkflowDefinition> = emptyList(),
    val workflowExecutions: List<WorkflowExecution> = emptyList(),
    val scheduleDefinitions: List<ScheduleDefinition> = emptyList(),
    val occurrences: List<Occurrence> = emptyList(),
    val devices: List<Device> = emptyList(),
    val deviceCommands: List<DeviceCommand> = emptyList(),
    val communicationSessions: List<CommunicationSession> = emptyList(),
    val contacts: List<Contact> = emptyList(),
)

interface IntegrationRuntimeRepository {
    suspend fun processRuntimeCycle(): AppResult<Map<String, Int>>
    suspend fun submitHubConfirmation(
        workflowExecutionId: String,
        interactionReference: String,
        evidenceType: String = "HUB_CONFIRMATION",
    ): AppResult<Unit>
}

interface HomeRepository {
    fun observeHomeSnapshot(): Flow<HomeRuntimeSnapshot>
}

interface ReminderRepository {
    suspend fun loadPresentation(executionId: String): ReminderPresentation?
}

interface ConnectivityRepository {
    fun observeOnline(): Flow<Boolean>
    suspend fun isOnline(): Boolean
    fun observeConnectivity(): Flow<ConnectivitySnapshot>
    suspend fun refreshBackendReachability(): ConnectivitySnapshot
}
