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
    @SerialName("client_checkpoint_sequence") val clientCheckpointSequence: Long? = null,
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
    @SerialName("occurrence_id") val occurrenceId: String? = null,
)

@Serializable
data class HubConfirmationResponseDto(
    @SerialName("workflow_execution_id") val workflowExecutionId: String,
    val status: String,
)

@Serializable
data class HubDeviceStateRequestDto(
    @SerialName("device_id") val deviceId: String,
    @SerialName("current_state") val currentState: JsonObject,
    @SerialName("is_online") val isOnline: Boolean = true,
)

@Serializable
data class HubDeviceStateResponseDto(
    @SerialName("device_id") val deviceId: String,
    @SerialName("operational_status") val operationalStatus: String,
)

@Serializable
data class HubRuntimeProcessResponseDto(
    @SerialName("due_occurrences") val dueOccurrences: Int = 0,
    @SerialName("workflow_timeouts") val workflowTimeouts: Int = 0,
    @SerialName("communication_timeouts") val communicationTimeouts: Int = 0,
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
data class HealthResponseDto(
    val status: String,
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

@Serializable
data class CallStartRequestDto(
    @SerialName("elder_id") val elderId: String,
    val channel: String,
    @SerialName("recipient_contact_id") val recipientContactId: String,
)

@Serializable
data class CallEndRequestDto(
    @SerialName("session_id") val sessionId: String,
)

@Serializable
data class CallJoinTokenRequestDto(
    @SerialName("elder_id") val elderId: String,
)

@Serializable
data class CallJoinResponseDto(
    val sessionId: String? = null,
    val joinToken: String,
    val expiresAt: String,
)

@Serializable
data class CallEndResponseDto(
    val status: String = "ended",
)

@Serializable
data class CommunicationSessionDto(
    val id: String,
    @SerialName("elder_id") val elderId: String,
    val channel: String,
    val status: String,
    val outcome: String? = null,
    @SerialName("initiated_at") val initiatedAt: String? = null,
)

@Serializable
data class SendMessageRequestDto(
    val direction: String,
    @SerialName("message_type") val messageType: String,
    val body: String? = null,
    @SerialName("attachment_id") val attachmentId: String? = null,
    @SerialName("idempotency_key") val idempotencyKey: String,
)

@Serializable
data class MessageAttachmentDto(
    val id: String = "",
    @SerialName("media_type") val mediaType: String? = null,
    @SerialName("file_size") val fileSize: Long = 0L,
    @SerialName("mime_type") val mimeType: String = "",
    @SerialName("duration_seconds") val durationSeconds: Double? = null,
    @SerialName("download_url") val downloadUrl: String = "",
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class MessageSenderDto(
    val id: String? = null,
    @SerialName("display_name") val displayName: String? = null,
    @SerialName("is_hub") val isHub: Boolean = false,
)

@Serializable
data class MessageResponseDto(
    val id: String,
    @SerialName("elder_id") val elderId: String,
    @SerialName("sender_user_id") val senderUserId: String? = null,
    @SerialName("sender_display_name") val senderDisplayName: String? = null,
    val sender: MessageSenderDto? = null,
    val direction: String,
    @SerialName("message_type") val messageType: String,
    val body: String? = null,
    val attachment: MessageAttachmentDto? = null,
    val status: String = "SENT",
    @SerialName("idempotency_key") val idempotencyKey: String = "",
    @SerialName("created_at") val createdAt: String = "",
    @SerialName("delivered_at") val deliveredAt: String? = null,
    @SerialName("read_at") val readAt: String? = null,
)

@Serializable
data class MessageStatusResponseDto(
    val id: String,
    val status: String,
    @SerialName("delivered_at") val deliveredAt: String? = null,
    @SerialName("read_at") val readAt: String? = null,
)

@Serializable
data class MediaUploadResponseDto(
    val id: String,
    @SerialName("media_type") val mediaType: String,
    @SerialName("file_size") val fileSize: Long,
    @SerialName("mime_type") val mimeType: String,
    @SerialName("duration_seconds") val durationSeconds: Double? = null,
    @SerialName("download_url") val downloadUrl: String,
    @SerialName("created_at") val createdAt: String,
)
