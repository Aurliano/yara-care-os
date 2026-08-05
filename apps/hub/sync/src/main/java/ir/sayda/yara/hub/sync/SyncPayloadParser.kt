package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.CommunicationSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.Device
import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.Prescription
import ir.sayda.yara.hub.core.domain.model.ScheduleDefinition
import ir.sayda.yara.hub.core.domain.model.WorkflowDefinition
import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.core.domain.repository.ReplicaSnapshotBundle
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncPayloadParser @Inject constructor() {
    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        explicitNulls = false
    }
    fun parseCareActivity(payloadJson: String, aggregateVersion: String): CareActivity {
        val payload = json.parseToJsonElement(payloadJson).jsonObject
        val now = System.currentTimeMillis()
        return CareActivity(
            id = payload.string("care_activity_id") ?: payload.string("id") ?: "",
            elderId = payload.string("elder_id") ?: "",
            activityType = payload.string("activity_type") ?: "",
            status = payload.string("status") ?: "ACTIVE",
            scheduleDefinitionId = payload.string("schedule_definition_id") ?: "",
            workflowDefinitionId = payload.string("workflow_definition_id") ?: "",
            displayTitle = payload.string("display_title") ?: "",
            displaySubtitle = payload.string("display_subtitle") ?: "",
            displayIcon = payload.string("display_icon") ?: "",
            confirmationRequirementJson = payload.string("confirmation_requirement_json") ?: "{}",
            compartmentAssignmentReference = payload.string("compartment_assignment_reference") ?: "",
            aggregateVersion = aggregateVersion.toLongOrNull() ?: payload.long("aggregate_version") ?: 0L,
            updatedAtEpochMillis = payload.long("updated_at_epoch_millis") ?: now,
        )
    }

    fun parseWorkflowExecution(payloadJson: String, aggregateVersion: String): WorkflowExecution {
        val payload = json.parseToJsonElement(payloadJson).jsonObject
        val now = System.currentTimeMillis()
        return WorkflowExecution(
            id = payload.string("workflow_execution_id") ?: payload.string("id") ?: "",
            occurrenceId = payload.string("occurrence_id") ?: "",
            workflowDefinitionId = payload.string("workflow_definition_id") ?: "",
            status = payload.string("status") ?: "PENDING",
            currentStep = payload.string("current_step") ?: "",
            postponeCount = payload.int("postpone_count") ?: 0,
            retryCount = payload.int("retry_count") ?: 0,
            escalationIndex = payload.int("escalation_index") ?: 0,
            currentActionJson = payload.string("current_action_json") ?: "{}",
            activeUntilEpochMillis = payload.long("active_until_epoch_millis"),
            startedAtEpochMillis = payload.long("started_at_epoch_millis"),
            completedAtEpochMillis = payload.long("completed_at_epoch_millis"),
            aggregateVersion = aggregateVersion.toLongOrNull() ?: payload.long("aggregate_version") ?: 0L,
            updatedAtEpochMillis = payload.long("updated_at_epoch_millis") ?: now,
        )
    }

    fun parseDevice(payloadJson: String, aggregateVersion: String): Device {
        val payload = json.parseToJsonElement(payloadJson).jsonObject
        val now = System.currentTimeMillis()
        return Device(
            id = payload.string("device_id") ?: payload.string("id") ?: "",
            deviceModelId = payload.string("device_model_id") ?: "",
            serialNumber = payload.string("serial_number") ?: "",
            operationalStatus = payload.string("operational_status") ?: "",
            currentStateJson = payload.jsonString("current_state") ?: payload.string("current_state_json") ?: "{}",
            configurationJson = payload.string("configuration_json") ?: "{}",
            lastSeenAtEpochMillis = payload.long("last_seen_at_epoch_millis"),
            aggregateVersion = aggregateVersion.toLongOrNull() ?: payload.long("aggregate_version") ?: 0L,
            updatedAtEpochMillis = payload.long("updated_at_epoch_millis") ?: now,
        )
    }

    fun parseCommunicationSession(payloadJson: String, aggregateVersion: String): CommunicationSession {
        val payload = json.parseToJsonElement(payloadJson).jsonObject
        val now = System.currentTimeMillis()
        return CommunicationSession(
            id = payload.string("communication_session_id") ?: payload.string("id") ?: "",
            elderId = payload.string("elder_id") ?: "",
            channel = payload.string("channel") ?: "",
            status = payload.string("status") ?: "",
            outcome = payload.string("outcome") ?: "",
            initiatedAtEpochMillis = payload.long("initiated_at_epoch_millis") ?: now,
            connectedAtEpochMillis = payload.long("connected_at_epoch_millis"),
            endedAtEpochMillis = payload.long("ended_at_epoch_millis"),
            externalExecutionReference = payload.string("external_execution_reference"),
            aggregateVersion = aggregateVersion.toLongOrNull() ?: payload.long("aggregate_version") ?: 0L,
            updatedAtEpochMillis = payload.long("updated_at_epoch_millis") ?: now,
        )
    }

    fun parseSnapshotBundle(payloadJson: String): ReplicaSnapshotBundle {
        val root = json.parseToJsonElement(payloadJson).jsonObject
        return ReplicaSnapshotBundle(
            careActivities = root.array("care_activities").map { parseCareActivity(it.toString(), "0") },
            prescriptions = root.array("prescriptions").mapNotNull { parsePrescription(it.jsonObject) },
            workflowDefinitions = root.array("workflow_definitions").mapNotNull { parseWorkflowDefinition(it.jsonObject) },
            workflowExecutions = root.array("workflow_executions").map { parseWorkflowExecution(it.toString(), "0") },
            scheduleDefinitions = root.array("schedule_definitions").mapNotNull { parseScheduleDefinition(it.jsonObject) },
            occurrences = root.array("occurrences").mapNotNull { parseOccurrence(it.jsonObject) },
            devices = root.array("devices").map { parseDevice(it.toString(), "0") },
            deviceCommands = emptyList(),
            communicationSessions = root.array("communication_sessions").map { parseCommunicationSession(it.toString(), "0") },
            contacts = root.array("contacts").mapNotNull { parseContact(it.jsonObject) },
        )
    }

    private fun parsePrescription(obj: JsonObject): Prescription? {
        val careActivityId = obj.string("care_activity_id") ?: return null
        return Prescription(
            careActivityId = careActivityId,
            medicationReference = obj.string("medication_reference") ?: "",
            dosageInformation = obj.string("dosage_information") ?: "",
            elderFriendlyDescription = obj.string("elder_friendly_description") ?: "",
            personalizedDescription = obj.string("personalized_description") ?: "",
            mediaReference = obj.string("media_reference"),
        )
    }

    private fun parseWorkflowDefinition(obj: JsonObject): WorkflowDefinition? {
        val id = obj.string("id") ?: obj.string("workflow_definition_id") ?: return null
        return WorkflowDefinition(
            id = id,
            code = obj.string("code") ?: "",
            name = obj.string("name") ?: "",
            status = obj.string("status") ?: "ACTIVE",
            definitionJson = obj.string("definition_json") ?: "{}",
            updatedAtEpochMillis = obj.long("updated_at_epoch_millis") ?: System.currentTimeMillis(),
        )
    }

    private fun parseScheduleDefinition(obj: JsonObject): ScheduleDefinition? {
        val id = obj.string("id") ?: obj.string("schedule_definition_id") ?: return null
        return ScheduleDefinition(
            id = id,
            ownerReference = obj.string("owner_reference") ?: "",
            recurrenceDefinitionJson = obj.string("recurrence_definition_json") ?: "{}",
            timezone = obj.string("timezone") ?: "UTC",
            startAtEpochMillis = obj.long("start_at_epoch_millis") ?: 0L,
            endAtEpochMillis = obj.long("end_at_epoch_millis"),
            status = obj.string("status") ?: "ACTIVE",
            updatedAtEpochMillis = obj.long("updated_at_epoch_millis") ?: System.currentTimeMillis(),
        )
    }

    private fun parseOccurrence(obj: JsonObject): Occurrence? {
        val id = obj.string("id") ?: obj.string("occurrence_id") ?: return null
        return Occurrence(
            id = id,
            scheduleDefinitionId = obj.string("schedule_definition_id") ?: "",
            scheduledForEpochMillis = obj.long("scheduled_for_epoch_millis") ?: 0L,
            status = obj.string("status") ?: "SCHEDULED",
            updatedAtEpochMillis = obj.long("updated_at_epoch_millis") ?: System.currentTimeMillis(),
        )
    }

    private fun parseContact(obj: JsonObject): Contact? {
        val id = obj.string("id") ?: obj.string("contact_id") ?: return null
        return Contact(
            id = id,
            elderId = obj.string("elder_id") ?: "",
            displayName = obj.string("display_name") ?: "",
            phone = obj.string("phone") ?: obj.string("phone_number") ?: "",
            communicationIdentitiesJson = obj.string("communication_identities_json") ?: "[]",
            preferredChannel = obj.string("preferred_channel") ?: "",
            photoReference = obj.string("photo_reference"),
            isPriority = obj.boolean("is_priority") ?: false,
            status = obj.string("status") ?: "ACTIVE",
            updatedAtEpochMillis = obj.long("updated_at_epoch_millis") ?: System.currentTimeMillis(),
        )
    }

    private fun JsonObject.string(key: String): String? =
        this[key]?.jsonPrimitive?.contentOrNull

    private fun JsonObject.int(key: String): Int? =
        this[key]?.jsonPrimitive?.intOrNull

    private fun JsonObject.long(key: String): Long? =
        this[key]?.jsonPrimitive?.longOrNull

    private fun JsonObject.boolean(key: String): Boolean? =
        this[key]?.jsonPrimitive?.contentOrNull?.toBooleanStrictOrNull()

    private fun JsonObject.jsonString(key: String): String? =
        this[key]?.let { json.encodeToString(kotlinx.serialization.json.JsonElement.serializer(), it) }

    private fun JsonObject.array(key: String) =
        this[key]?.jsonArray?.map { it } ?: emptyList()
}
