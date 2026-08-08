package ir.sayda.yara.hub.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class TokenRequestDto(
    val phone: String,
    val password: String,
)

@Serializable
data class TokenResponseDto(
    val access: String,
    val refresh: String,
)

@Serializable
data class TokenRefreshRequestDto(
    val refresh: String,
)

@Serializable
data class HubSyncStartRequestDto(
    val direction: String,
    @SerialName("idempotency_key") val idempotencyKey: String,
)

@Serializable
data class HubSyncStartResponseDto(
    @SerialName("session_id") val sessionId: String,
    val status: String,
    @SerialName("synchronization_token") val synchronizationToken: String,
)

@Serializable
data class HubSyncPayloadRequestDto(
    @SerialName("aggregate_reference") val aggregateReference: String,
    @SerialName("aggregate_version") val aggregateVersion: String,
    val payload: JsonObject,
    @SerialName("payload_type") val payloadType: String,
    @SerialName("payload_hash") val payloadHash: String,
    @SerialName("idempotency_key") val idempotencyKey: String,
)

@Serializable
data class HubSyncOperationResponseDto(
    @SerialName("operation_id") val operationId: String,
    val status: String,
)

@Serializable
data class HubSyncCompleteResponseDto(
    val status: String,
    @SerialName("operations_applied") val operationsApplied: Int = 0,
)

@Serializable
data class HubConfirmationRequestDto(
    @SerialName("workflow_execution_id") val workflowExecutionId: String,
    @SerialName("interaction_reference") val interactionReference: String,
    @SerialName("evidence_type") val evidenceType: String = "HUB_CONFIRMATION",
)

@Serializable
data class HubConfirmationResponseDto(
    @SerialName("workflow_execution_id") val workflowExecutionId: String,
    val status: String,
)

@Serializable
data class HubRuntimeProcessResponseDto(
    @SerialName("due_occurrences") val dueOccurrences: Int = 0,
    @SerialName("workflow_timeouts") val workflowTimeouts: Int = 0,
    @SerialName("events_processed") val eventsProcessed: Int = 0,
)

@Serializable
data class SyncOperationDto(
    val id: String,
    @SerialName("operation_type") val operationType: String,
    @SerialName("aggregate_reference") val aggregateReference: String,
    @SerialName("aggregate_version") val aggregateVersion: String,
    @SerialName("payload_type") val payloadType: String,
    @SerialName("payload_hash") val payloadHash: String,
    val payload: JsonObject? = null,
    val status: String,
    @SerialName("failure_reason") val failureReason: String? = null,
    @SerialName("started_at") val startedAt: String? = null,
    @SerialName("applied_at") val appliedAt: String? = null,
)

@Serializable
data class SyncSessionResponseDto(
    val id: String,
    @SerialName("replica_identifier") val replicaIdentifier: String,
    val direction: String,
    val status: String,
    @SerialName("synchronization_token") val synchronizationToken: String,
)

@Serializable
data class SyncCheckpointResponseDto(
    @SerialName("replica_identifier") val replicaIdentifier: String,
    @SerialName("checkpoint_sequence") val checkpointSequence: Long,
    @SerialName("checkpoint_token") val checkpointToken: String? = null,
)

@Serializable
data class ApiErrorDto(
    val detail: String? = null,
    val code: String? = null,
)

@Serializable
data class HubProvisionRegisterRequestDto(
    @SerialName("serial_number") val serialNumber: String,
    @SerialName("device_model_code") val deviceModelCode: String,
)

@Serializable
data class HubProvisionRegisterResponseDto(
    @SerialName("device_id") val deviceId: String,
    @SerialName("replica_identifier") val replicaIdentifier: String,
    @SerialName("provisioning_state") val provisioningState: String,
    @SerialName("provisioned_at") val provisionedAt: String,
    @SerialName("elder_id") val elderId: String? = null,
)

@Serializable
data class HubProvisionAuthenticateRequestDto(
    @SerialName("device_id") val deviceId: String,
    val phone: String,
    val password: String,
)

@Serializable
data class HubProvisionAuthenticateResponseDto(
    @SerialName("device_id") val deviceId: String,
    @SerialName("replica_identifier") val replicaIdentifier: String,
    @SerialName("provisioning_state") val provisioningState: String,
    @SerialName("provisioned_at") val provisionedAt: String,
    @SerialName("authenticated_at") val authenticatedAt: String? = null,
    @SerialName("elder_id") val elderId: String? = null,
    val access: String,
    val refresh: String,
)

@Serializable
data class HubProvisionStatusResponseDto(
    @SerialName("device_id") val deviceId: String,
    @SerialName("replica_identifier") val replicaIdentifier: String? = null,
    @SerialName("provisioning_state") val provisioningState: String,
    @SerialName("provisioned_at") val provisionedAt: String? = null,
    @SerialName("authenticated_at") val authenticatedAt: String? = null,
    @SerialName("elder_id") val elderId: String? = null,
    val revoked: Boolean = false,
)

@Serializable
data class HubProvisionRevokeRequestDto(
    @SerialName("device_id") val deviceId: String,
)
