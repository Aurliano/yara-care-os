package ir.sayda.yara.hub.database.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "care_activity",
    indices = [Index("elder_id"), Index("status")],
)
data class CareActivityEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "elder_id") val elderId: String,
    @ColumnInfo(name = "activity_type") val activityType: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "schedule_definition_id") val scheduleDefinitionId: String,
    @ColumnInfo(name = "workflow_definition_id") val workflowDefinitionId: String,
    @ColumnInfo(name = "display_title") val displayTitle: String,
    @ColumnInfo(name = "display_subtitle") val displaySubtitle: String,
    @ColumnInfo(name = "display_icon") val displayIcon: String,
    @ColumnInfo(name = "confirmation_requirement_json") val confirmationRequirementJson: String,
    @ColumnInfo(name = "compartment_assignment_reference") val compartmentAssignmentReference: String,
    @ColumnInfo(name = "aggregate_version") val aggregateVersion: Long,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(tableName = "prescription")
data class PrescriptionEntity(
    @PrimaryKey @ColumnInfo(name = "care_activity_id") val careActivityId: String,
    @ColumnInfo(name = "medication_reference") val medicationReference: String,
    @ColumnInfo(name = "dosage_information") val dosageInformation: String,
    @ColumnInfo(name = "elder_friendly_description") val elderFriendlyDescription: String,
    @ColumnInfo(name = "personalized_description") val personalizedDescription: String,
    @ColumnInfo(name = "media_reference") val mediaReference: String?,
)

@Entity(
    tableName = "workflow_definition",
    indices = [Index(value = ["code"], unique = true)],
)
data class WorkflowDefinitionEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "code") val code: String,
    @ColumnInfo(name = "name") val name: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "definition_json") val definitionJson: String,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "workflow_execution",
    indices = [
        Index(value = ["occurrence_id"], unique = true),
        Index("status"),
        Index("active_until_epoch_millis"),
    ],
)
data class WorkflowExecutionEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "occurrence_id") val occurrenceId: String,
    @ColumnInfo(name = "workflow_definition_id") val workflowDefinitionId: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "current_step") val currentStep: String,
    @ColumnInfo(name = "postpone_count") val postponeCount: Int,
    @ColumnInfo(name = "retry_count") val retryCount: Int,
    @ColumnInfo(name = "escalation_index") val escalationIndex: Int,
    @ColumnInfo(name = "current_action_json") val currentActionJson: String,
    @ColumnInfo(name = "active_until_epoch_millis") val activeUntilEpochMillis: Long?,
    @ColumnInfo(name = "started_at_epoch_millis") val startedAtEpochMillis: Long?,
    @ColumnInfo(name = "completed_at_epoch_millis") val completedAtEpochMillis: Long?,
    @ColumnInfo(name = "aggregate_version") val aggregateVersion: Long,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "schedule_definition",
    indices = [Index("owner_reference"), Index("status")],
)
data class ScheduleDefinitionEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "owner_reference") val ownerReference: String,
    @ColumnInfo(name = "recurrence_definition_json") val recurrenceDefinitionJson: String,
    @ColumnInfo(name = "timezone") val timezone: String,
    @ColumnInfo(name = "start_at_epoch_millis") val startAtEpochMillis: Long,
    @ColumnInfo(name = "end_at_epoch_millis") val endAtEpochMillis: Long?,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "occurrence",
    indices = [
        Index("schedule_definition_id"),
        Index("status"),
        Index(value = ["schedule_definition_id", "scheduled_for_epoch_millis"], unique = true),
    ],
)
data class OccurrenceEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "schedule_definition_id") val scheduleDefinitionId: String,
    @ColumnInfo(name = "scheduled_for_epoch_millis") val scheduledForEpochMillis: Long,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "device",
    indices = [Index(value = ["serial_number"], unique = true), Index("operational_status")],
)
data class DeviceEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "device_model_id") val deviceModelId: String,
    @ColumnInfo(name = "serial_number") val serialNumber: String,
    @ColumnInfo(name = "operational_status") val operationalStatus: String,
    @ColumnInfo(name = "current_state_json") val currentStateJson: String,
    @ColumnInfo(name = "configuration_json") val configurationJson: String,
    @ColumnInfo(name = "last_seen_at_epoch_millis") val lastSeenAtEpochMillis: Long?,
    @ColumnInfo(name = "aggregate_version") val aggregateVersion: Long,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "device_command",
    indices = [Index("target_device_id"), Index("status"), Index(value = ["idempotency_key"], unique = true)],
)
data class DeviceCommandEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "target_device_id") val targetDeviceId: String,
    @ColumnInfo(name = "command_type") val commandType: String,
    @ColumnInfo(name = "parameters_json") val parametersJson: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "expires_at_epoch_millis") val expiresAtEpochMillis: Long,
    @ColumnInfo(name = "result_json") val resultJson: String,
    @ColumnInfo(name = "failure_reason") val failureReason: String,
    @ColumnInfo(name = "idempotency_key") val idempotencyKey: String,
    @ColumnInfo(name = "execution_reference") val executionReference: String?,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "communication_session",
    indices = [Index("elder_id"), Index("status"), Index("external_execution_reference")],
)
data class CommunicationSessionEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "elder_id") val elderId: String,
    @ColumnInfo(name = "channel") val channel: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "outcome") val outcome: String,
    @ColumnInfo(name = "initiated_at_epoch_millis") val initiatedAtEpochMillis: Long,
    @ColumnInfo(name = "connected_at_epoch_millis") val connectedAtEpochMillis: Long?,
    @ColumnInfo(name = "ended_at_epoch_millis") val endedAtEpochMillis: Long?,
    @ColumnInfo(name = "external_execution_reference") val externalExecutionReference: String?,
    @ColumnInfo(name = "aggregate_version") val aggregateVersion: Long,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "contact",
    indices = [Index("elder_id"), Index("status"), Index("is_priority")],
)
data class ContactEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "elder_id") val elderId: String,
    @ColumnInfo(name = "display_name") val displayName: String,
    @ColumnInfo(name = "phone") val phone: String,
    @ColumnInfo(name = "communication_identities_json") val communicationIdentitiesJson: String,
    @ColumnInfo(name = "preferred_channel") val preferredChannel: String,
    @ColumnInfo(name = "photo_reference") val photoReference: String?,
    @ColumnInfo(name = "is_priority") val isPriority: Boolean,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(tableName = "replica_state")
data class ReplicaStateEntity(
    @PrimaryKey @ColumnInfo(name = "replica_identifier") val replicaIdentifier: String,
    @ColumnInfo(name = "replica_type") val replicaType: String,
    @ColumnInfo(name = "health") val health: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "checkpoint_sequence") val checkpointSequence: Long,
    @ColumnInfo(name = "checkpoint_token") val checkpointToken: String?,
    @ColumnInfo(name = "last_successful_sync_epoch_millis") val lastSuccessfulSyncEpochMillis: Long?,
)

@Entity(
    tableName = "pending_evidence",
    indices = [
        Index("workflow_execution_id"),
        Index("status"),
        Index("correlation_id"),
        Index(value = ["idempotency_key"], unique = true),
    ],
)
data class PendingEvidenceEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "workflow_execution_id") val workflowExecutionId: String,
    @ColumnInfo(name = "evidence_type") val evidenceType: String,
    @ColumnInfo(name = "interaction_reference") val interactionReference: String,
    @ColumnInfo(name = "payload_json") val payloadJson: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "correlation_id") val correlationId: String,
    @ColumnInfo(name = "idempotency_key") val idempotencyKey: String,
    @ColumnInfo(name = "retry_count") val retryCount: Int,
    @ColumnInfo(name = "created_at_epoch_millis") val createdAtEpochMillis: Long,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
    @ColumnInfo(name = "last_attempt_at_epoch_millis") val lastAttemptAtEpochMillis: Long?,
    @ColumnInfo(name = "last_error") val lastError: String?,
)

@Entity(
    tableName = "outbox_entry",
    indices = [Index("status"), Index("priority"), Index(value = ["idempotency_key"], unique = true)],
)
data class OutboxEntryEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "operation_type") val operationType: String,
    @ColumnInfo(name = "payload_json") val payloadJson: String,
    @ColumnInfo(name = "idempotency_key") val idempotencyKey: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "retry_count") val retryCount: Int,
    @ColumnInfo(name = "priority") val priority: Int,
    @ColumnInfo(name = "created_at_epoch_millis") val createdAtEpochMillis: Long,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
    @ColumnInfo(name = "last_attempt_at_epoch_millis") val lastAttemptAtEpochMillis: Long?,
    @ColumnInfo(name = "last_error") val lastError: String?,
)

@Entity(tableName = "runtime_state")
data class RuntimeStateEntity(
    @PrimaryKey @ColumnInfo(name = "component_id") val componentId: String,
    @ColumnInfo(name = "lifecycle_state") val lifecycleState: String,
    @ColumnInfo(name = "state_payload_json") val statePayloadJson: String,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)

@Entity(
    tableName = "sync_session_local",
    indices = [Index("status")],
)
data class SyncSessionLocalEntity(
    @PrimaryKey @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "direction") val direction: String,
    @ColumnInfo(name = "status") val status: String,
    @ColumnInfo(name = "synchronization_token") val synchronizationToken: String,
    @ColumnInfo(name = "started_at_epoch_millis") val startedAtEpochMillis: Long,
)

@Entity(
    tableName = "sync_conflict",
    indices = [Index("aggregate_reference"), Index("session_id")],
)
data class SyncConflictEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "aggregate_reference") val aggregateReference: String,
    @ColumnInfo(name = "conflict_type") val conflictType: String,
    @ColumnInfo(name = "local_version") val localVersion: String?,
    @ColumnInfo(name = "remote_version") val remoteVersion: String?,
    @ColumnInfo(name = "session_id") val sessionId: String?,
    @ColumnInfo(name = "detected_at_epoch_millis") val detectedAtEpochMillis: Long,
    @ColumnInfo(name = "payload_json") val payloadJson: String,
)

@Entity(tableName = "local_call_session")
data class LocalCallSessionEntity(
    @PrimaryKey @ColumnInfo(name = "id") val id: String,
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "elder_id") val elderId: String,
    @ColumnInfo(name = "channel") val channel: String,
    @ColumnInfo(name = "recipient_contact_id") val recipientContactId: String,
    @ColumnInfo(name = "runtime_state") val runtimeState: String,
    @ColumnInfo(name = "join_token") val joinToken: String,
    @ColumnInfo(name = "expires_at_epoch_millis") val expiresAtEpochMillis: Long,
    @ColumnInfo(name = "updated_at_epoch_millis") val updatedAtEpochMillis: Long,
)
