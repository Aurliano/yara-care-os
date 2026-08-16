package ir.sayda.yara.hub.database.mapper

import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.CommunicationSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.Device
import ir.sayda.yara.hub.core.domain.model.DeviceCommand
import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.OutboxEntry
import ir.sayda.yara.hub.core.domain.model.PendingEvidence
import ir.sayda.yara.hub.core.domain.model.Prescription
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.domain.model.RuntimeStateRecord
import ir.sayda.yara.hub.core.domain.model.ScheduleDefinition
import ir.sayda.yara.hub.core.domain.model.SyncSession
import ir.sayda.yara.hub.core.domain.model.WorkflowDefinition
import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.database.entity.CareActivityEntity
import ir.sayda.yara.hub.database.entity.CommunicationSessionEntity
import ir.sayda.yara.hub.database.entity.ContactEntity
import ir.sayda.yara.hub.database.entity.DeviceCommandEntity
import ir.sayda.yara.hub.database.entity.DeviceEntity
import ir.sayda.yara.hub.database.entity.OccurrenceEntity
import ir.sayda.yara.hub.database.entity.OutboxEntryEntity
import ir.sayda.yara.hub.database.entity.PendingEvidenceEntity
import ir.sayda.yara.hub.database.entity.PrescriptionEntity
import ir.sayda.yara.hub.database.entity.ReplicaStateEntity
import ir.sayda.yara.hub.database.entity.RuntimeStateEntity
import ir.sayda.yara.hub.database.entity.ScheduleDefinitionEntity
import ir.sayda.yara.hub.database.entity.SyncSessionLocalEntity
import ir.sayda.yara.hub.database.entity.WorkflowDefinitionEntity
import ir.sayda.yara.hub.database.entity.WorkflowExecutionEntity

fun CareActivityEntity.toDomain() = CareActivity(
    id = id,
    elderId = elderId,
    activityType = activityType,
    status = status,
    scheduleDefinitionId = scheduleDefinitionId,
    workflowDefinitionId = workflowDefinitionId,
    displayTitle = displayTitle,
    displaySubtitle = displaySubtitle,
    displayIcon = displayIcon,
    confirmationRequirementJson = confirmationRequirementJson,
    compartmentAssignmentReference = compartmentAssignmentReference,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun CareActivity.toEntity() = CareActivityEntity(
    id = id,
    elderId = elderId,
    activityType = activityType,
    status = status,
    scheduleDefinitionId = scheduleDefinitionId,
    workflowDefinitionId = workflowDefinitionId,
    displayTitle = displayTitle,
    displaySubtitle = displaySubtitle,
    displayIcon = displayIcon,
    confirmationRequirementJson = confirmationRequirementJson,
    compartmentAssignmentReference = compartmentAssignmentReference,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun PrescriptionEntity.toDomain() = Prescription(
    careActivityId = careActivityId,
    medicationReference = medicationReference,
    dosageInformation = dosageInformation,
    elderFriendlyDescription = elderFriendlyDescription,
    personalizedDescription = personalizedDescription,
    mediaReference = mediaReference,
)

fun Prescription.toEntity() = PrescriptionEntity(
    careActivityId = careActivityId,
    medicationReference = medicationReference,
    dosageInformation = dosageInformation,
    elderFriendlyDescription = elderFriendlyDescription,
    personalizedDescription = personalizedDescription,
    mediaReference = mediaReference,
)

fun WorkflowDefinitionEntity.toDomain() = WorkflowDefinition(
    id = id,
    code = code,
    name = name,
    status = status,
    definitionJson = definitionJson,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun WorkflowDefinition.toEntity() = WorkflowDefinitionEntity(
    id = id,
    code = code,
    name = name,
    status = status,
    definitionJson = definitionJson,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun WorkflowExecutionEntity.toDomain() = WorkflowExecution(
    id = id,
    occurrenceId = occurrenceId,
    workflowDefinitionId = workflowDefinitionId,
    status = status,
    currentStep = currentStep,
    postponeCount = postponeCount,
    retryCount = retryCount,
    escalationIndex = escalationIndex,
    currentActionJson = currentActionJson,
    activeUntilEpochMillis = activeUntilEpochMillis,
    startedAtEpochMillis = startedAtEpochMillis,
    completedAtEpochMillis = completedAtEpochMillis,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun WorkflowExecution.toEntity() = WorkflowExecutionEntity(
    id = id,
    occurrenceId = occurrenceId,
    workflowDefinitionId = workflowDefinitionId,
    status = status,
    currentStep = currentStep,
    postponeCount = postponeCount,
    retryCount = retryCount,
    escalationIndex = escalationIndex,
    currentActionJson = currentActionJson,
    activeUntilEpochMillis = activeUntilEpochMillis,
    startedAtEpochMillis = startedAtEpochMillis,
    completedAtEpochMillis = completedAtEpochMillis,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun ScheduleDefinitionEntity.toDomain() = ScheduleDefinition(
    id = id,
    ownerReference = ownerReference,
    recurrenceDefinitionJson = recurrenceDefinitionJson,
    timezone = timezone,
    startAtEpochMillis = startAtEpochMillis,
    endAtEpochMillis = endAtEpochMillis,
    status = status,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun ScheduleDefinition.toEntity() = ScheduleDefinitionEntity(
    id = id,
    ownerReference = ownerReference,
    recurrenceDefinitionJson = recurrenceDefinitionJson,
    timezone = timezone,
    startAtEpochMillis = startAtEpochMillis,
    endAtEpochMillis = endAtEpochMillis,
    status = status,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun OccurrenceEntity.toDomain() = Occurrence(
    id = id,
    scheduleDefinitionId = scheduleDefinitionId,
    scheduledForEpochMillis = scheduledForEpochMillis,
    status = status,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun Occurrence.toEntity() = OccurrenceEntity(
    id = id,
    scheduleDefinitionId = scheduleDefinitionId,
    scheduledForEpochMillis = scheduledForEpochMillis,
    status = status,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun DeviceEntity.toDomain() = Device(
    id = id,
    deviceModelId = deviceModelId,
    serialNumber = serialNumber,
    operationalStatus = operationalStatus,
    currentStateJson = currentStateJson,
    configurationJson = configurationJson,
    lastSeenAtEpochMillis = lastSeenAtEpochMillis,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun Device.toEntity() = DeviceEntity(
    id = id,
    deviceModelId = deviceModelId,
    serialNumber = serialNumber,
    operationalStatus = operationalStatus,
    currentStateJson = currentStateJson,
    configurationJson = configurationJson,
    lastSeenAtEpochMillis = lastSeenAtEpochMillis,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun DeviceCommandEntity.toDomain() = DeviceCommand(
    id = id,
    targetDeviceId = targetDeviceId,
    commandType = commandType,
    parametersJson = parametersJson,
    status = status,
    expiresAtEpochMillis = expiresAtEpochMillis,
    resultJson = resultJson,
    failureReason = failureReason,
    idempotencyKey = idempotencyKey,
    executionReference = executionReference,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun DeviceCommand.toEntity() = DeviceCommandEntity(
    id = id,
    targetDeviceId = targetDeviceId,
    commandType = commandType,
    parametersJson = parametersJson,
    status = status,
    expiresAtEpochMillis = expiresAtEpochMillis,
    resultJson = resultJson,
    failureReason = failureReason,
    idempotencyKey = idempotencyKey,
    executionReference = executionReference,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun CommunicationSessionEntity.toDomain() = CommunicationSession(
    id = id,
    elderId = elderId,
    channel = channel,
    status = status,
    outcome = outcome,
    initiatedAtEpochMillis = initiatedAtEpochMillis,
    connectedAtEpochMillis = connectedAtEpochMillis,
    endedAtEpochMillis = endedAtEpochMillis,
    externalExecutionReference = externalExecutionReference,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun CommunicationSession.toEntity() = CommunicationSessionEntity(
    id = id,
    elderId = elderId,
    channel = channel,
    status = status,
    outcome = outcome,
    initiatedAtEpochMillis = initiatedAtEpochMillis,
    connectedAtEpochMillis = connectedAtEpochMillis,
    endedAtEpochMillis = endedAtEpochMillis,
    externalExecutionReference = externalExecutionReference,
    aggregateVersion = aggregateVersion,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun ContactEntity.toDomain() = Contact(
    id = id,
    elderId = elderId,
    displayName = displayName,
    phone = phone,
    communicationIdentitiesJson = communicationIdentitiesJson,
    preferredChannel = preferredChannel,
    photoReference = photoReference,
    isPriority = isPriority,
    status = status,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun Contact.toEntity() = ContactEntity(
    id = id,
    elderId = elderId,
    displayName = displayName,
    phone = phone,
    communicationIdentitiesJson = communicationIdentitiesJson,
    preferredChannel = preferredChannel,
    photoReference = photoReference,
    isPriority = isPriority,
    status = status,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun ReplicaStateEntity.toDomain() = ReplicaState(
    replicaIdentifier = replicaIdentifier,
    replicaType = replicaType,
    health = health,
    status = status,
    checkpointSequence = checkpointSequence,
    checkpointToken = checkpointToken,
    lastSuccessfulSyncEpochMillis = lastSuccessfulSyncEpochMillis,
)

fun ReplicaState.toEntity() = ReplicaStateEntity(
    replicaIdentifier = replicaIdentifier,
    replicaType = replicaType,
    health = health,
    status = status,
    checkpointSequence = checkpointSequence,
    checkpointToken = checkpointToken,
    lastSuccessfulSyncEpochMillis = lastSuccessfulSyncEpochMillis,
)

fun PendingEvidenceEntity.toDomain() = PendingEvidence(
    id = id,
    workflowExecutionId = workflowExecutionId,
    evidenceType = evidenceType,
    interactionReference = interactionReference,
    payloadJson = payloadJson,
    status = status,
    correlationId = correlationId,
    idempotencyKey = idempotencyKey,
    retryCount = retryCount,
    createdAtEpochMillis = createdAtEpochMillis,
    updatedAtEpochMillis = updatedAtEpochMillis,
    lastAttemptAtEpochMillis = lastAttemptAtEpochMillis,
    lastError = lastError,
)

fun PendingEvidence.toEntity() = PendingEvidenceEntity(
    id = id,
    workflowExecutionId = workflowExecutionId,
    evidenceType = evidenceType,
    interactionReference = interactionReference,
    payloadJson = payloadJson,
    status = status,
    correlationId = correlationId,
    idempotencyKey = idempotencyKey,
    retryCount = retryCount,
    createdAtEpochMillis = createdAtEpochMillis,
    updatedAtEpochMillis = updatedAtEpochMillis,
    lastAttemptAtEpochMillis = lastAttemptAtEpochMillis,
    lastError = lastError,
)

fun OutboxEntryEntity.toDomain() = OutboxEntry(
    id = id,
    operationType = operationType,
    payloadJson = payloadJson,
    idempotencyKey = idempotencyKey,
    status = status,
    retryCount = retryCount,
    priority = priority,
    createdAtEpochMillis = createdAtEpochMillis,
    updatedAtEpochMillis = updatedAtEpochMillis,
    lastAttemptAtEpochMillis = lastAttemptAtEpochMillis,
    lastError = lastError,
)

fun OutboxEntry.toEntity() = OutboxEntryEntity(
    id = id,
    operationType = operationType,
    payloadJson = payloadJson,
    idempotencyKey = idempotencyKey,
    status = status,
    retryCount = retryCount,
    priority = priority,
    createdAtEpochMillis = createdAtEpochMillis,
    updatedAtEpochMillis = updatedAtEpochMillis,
    lastAttemptAtEpochMillis = lastAttemptAtEpochMillis,
    lastError = lastError,
)

fun RuntimeStateEntity.toDomain() = RuntimeStateRecord(
    componentId = componentId,
    lifecycleState = lifecycleState,
    statePayloadJson = statePayloadJson,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun RuntimeStateRecord.toEntity() = RuntimeStateEntity(
    componentId = componentId,
    lifecycleState = lifecycleState,
    statePayloadJson = statePayloadJson,
    updatedAtEpochMillis = updatedAtEpochMillis,
)

fun SyncSessionLocalEntity.toDomain() = SyncSession(
    sessionId = sessionId,
    direction = direction,
    status = status,
    synchronizationToken = synchronizationToken,
    startedAtEpochMillis = startedAtEpochMillis,
)

fun SyncSession.toEntity() = SyncSessionLocalEntity(
    sessionId = sessionId,
    direction = direction,
    status = status,
    synchronizationToken = synchronizationToken,
    startedAtEpochMillis = startedAtEpochMillis,
)

fun ir.sayda.yara.hub.database.entity.SyncConflictEntity.toDomain() = ir.sayda.yara.hub.core.sync.SyncConflictRecord(
    id = id,
    aggregateReference = aggregateReference,
    conflictType = ir.sayda.yara.hub.core.sync.ConflictType.valueOf(conflictType),
    localVersion = localVersion,
    remoteVersion = remoteVersion,
    sessionId = sessionId,
    detectedAtEpochMillis = detectedAtEpochMillis,
    payloadJson = payloadJson,
)

fun ir.sayda.yara.hub.core.sync.SyncConflictRecord.toEntity() = ir.sayda.yara.hub.database.entity.SyncConflictEntity(
    id = id,
    aggregateReference = aggregateReference,
    conflictType = conflictType.name,
    localVersion = localVersion,
    remoteVersion = remoteVersion,
    sessionId = sessionId,
    detectedAtEpochMillis = detectedAtEpochMillis,
    payloadJson = payloadJson,
)

private const val CURRENT_CALL_ROW_ID = "current"

fun ir.sayda.yara.hub.database.entity.LocalCallSessionEntity.toDomain() =
    ir.sayda.yara.hub.core.domain.model.CallSession(
        sessionId = sessionId,
        elderId = elderId,
        channel = channel,
        recipientContactId = recipientContactId,
        runtimeState = ir.sayda.yara.hub.core.domain.model.CallRuntimeState.valueOf(runtimeState),
        joinToken = joinToken,
        expiresAtEpochMillis = expiresAtEpochMillis,
        updatedAtEpochMillis = updatedAtEpochMillis,
    )

fun ir.sayda.yara.hub.core.domain.model.CallSession.toEntity() =
    ir.sayda.yara.hub.database.entity.LocalCallSessionEntity(
        id = CURRENT_CALL_ROW_ID,
        sessionId = sessionId,
        elderId = elderId,
        channel = channel,
        recipientContactId = recipientContactId,
        runtimeState = runtimeState.name,
        joinToken = joinToken,
        expiresAtEpochMillis = expiresAtEpochMillis,
        updatedAtEpochMillis = updatedAtEpochMillis,
    )
