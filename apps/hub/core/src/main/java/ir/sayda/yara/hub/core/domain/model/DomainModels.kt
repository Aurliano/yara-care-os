package ir.sayda.yara.hub.core.domain.model

data class CareActivity(
    val id: String,
    val elderId: String,
    val activityType: String,
    val status: String,
    val scheduleDefinitionId: String,
    val workflowDefinitionId: String,
    val displayTitle: String,
    val displaySubtitle: String,
    val displayIcon: String,
    val confirmationRequirementJson: String,
    val compartmentAssignmentReference: String,
    val aggregateVersion: Long,
    val updatedAtEpochMillis: Long,
)

data class Prescription(
    val careActivityId: String,
    val medicationReference: String,
    val dosageInformation: String,
    val elderFriendlyDescription: String,
    val personalizedDescription: String,
    val mediaReference: String?,
)

data class WorkflowDefinition(
    val id: String,
    val code: String,
    val name: String,
    val status: String,
    val definitionJson: String,
    val updatedAtEpochMillis: Long,
)

data class WorkflowExecution(
    val id: String,
    val occurrenceId: String,
    val workflowDefinitionId: String,
    val status: String,
    val currentStep: String,
    val postponeCount: Int,
    val retryCount: Int,
    val escalationIndex: Int,
    val currentActionJson: String,
    val activeUntilEpochMillis: Long?,
    val startedAtEpochMillis: Long?,
    val completedAtEpochMillis: Long?,
    val aggregateVersion: Long,
    val updatedAtEpochMillis: Long,
)

data class ScheduleDefinition(
    val id: String,
    val ownerReference: String,
    val recurrenceDefinitionJson: String,
    val timezone: String,
    val startAtEpochMillis: Long,
    val endAtEpochMillis: Long?,
    val status: String,
    val updatedAtEpochMillis: Long,
)

data class Occurrence(
    val id: String,
    val scheduleDefinitionId: String,
    val scheduledForEpochMillis: Long,
    val status: String,
    val updatedAtEpochMillis: Long,
)

data class Device(
    val id: String,
    val deviceModelId: String,
    val serialNumber: String,
    val operationalStatus: String,
    val currentStateJson: String,
    val configurationJson: String,
    val lastSeenAtEpochMillis: Long?,
    val aggregateVersion: Long,
    val updatedAtEpochMillis: Long,
)

data class DeviceCommand(
    val id: String,
    val targetDeviceId: String,
    val commandType: String,
    val parametersJson: String,
    val status: String,
    val expiresAtEpochMillis: Long,
    val resultJson: String,
    val failureReason: String,
    val idempotencyKey: String,
    val executionReference: String?,
    val updatedAtEpochMillis: Long,
)

data class CommunicationSession(
    val id: String,
    val elderId: String,
    val channel: String,
    val status: String,
    val outcome: String,
    val initiatedAtEpochMillis: Long,
    val connectedAtEpochMillis: Long?,
    val endedAtEpochMillis: Long?,
    val externalExecutionReference: String?,
    val aggregateVersion: Long,
    val updatedAtEpochMillis: Long,
)

data class Contact(
    val id: String,
    val elderId: String,
    val displayName: String,
    val phone: String,
    val communicationIdentitiesJson: String,
    val preferredChannel: String,
    val photoReference: String?,
    val isPriority: Boolean,
    val status: String,
    val updatedAtEpochMillis: Long,
)

data class ReplicaState(
    val replicaIdentifier: String,
    val replicaType: String,
    val health: String,
    val status: String,
    val checkpointSequence: Long,
    val checkpointToken: String?,
    val lastSuccessfulSyncEpochMillis: Long?,
)

data class PendingEvidence(
    val id: String,
    val workflowExecutionId: String,
    val evidenceType: String,
    val interactionReference: String,
    val payloadJson: String,
    val status: String,
    val correlationId: String,
    val idempotencyKey: String,
    val retryCount: Int,
    val createdAtEpochMillis: Long,
    val updatedAtEpochMillis: Long,
    val lastAttemptAtEpochMillis: Long?,
    val lastError: String?,
)

data class OutboxEntry(
    val id: String,
    val operationType: String,
    val payloadJson: String,
    val idempotencyKey: String,
    val status: String,
    val retryCount: Int,
    val priority: Int,
    val createdAtEpochMillis: Long,
    val updatedAtEpochMillis: Long,
    val lastAttemptAtEpochMillis: Long?,
    val lastError: String?,
)

data class RuntimeStateRecord(
    val componentId: String,
    val lifecycleState: String,
    val statePayloadJson: String,
    val updatedAtEpochMillis: Long,
)

data class SyncSession(
    val sessionId: String,
    val direction: String,
    val status: String,
    val synchronizationToken: String,
    val startedAtEpochMillis: Long,
)

data class HubIdentity(
    val deviceId: String,
    val replicaId: String,
    val elderId: String?,
    val accessToken: String,
    val refreshToken: String,
    val tokenExpiresAtEpochMillis: Long,
)

data class HomeRuntimeSnapshot(
    val elderDisplayName: String,
    val activeExecutions: List<WorkflowExecution>,
    val priorityContacts: List<Contact>,
    val replicaHealth: String,
    val isOnline: Boolean,
)
