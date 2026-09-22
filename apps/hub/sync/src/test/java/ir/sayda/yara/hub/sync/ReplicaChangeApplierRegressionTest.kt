package ir.sayda.yara.hub.sync

import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.DeviceReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.sync.ReplicaDomain
import ir.sayda.yara.hub.core.sync.SyncOperation
import ir.sayda.yara.hub.core.sync.SyncOperationType
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class ReplicaChangeApplierRegressionTest {

    private val careRepo = mockk<CareReplicaRepository>(relaxed = true)
    private val schedulingRepo = mockk<SchedulingReplicaRepository>(relaxed = true)
    private val workflowRepo = mockk<WorkflowReplicaRepository>(relaxed = true)
    private val deviceRepo = mockk<DeviceReplicaRepository>(relaxed = true)
    private val commRepo = mockk<CommunicationReplicaRepository>(relaxed = true)
    private val snapshotApplier = mockk<SnapshotApplier>(relaxed = true)
    private val conflictRecorder = mockk<ConflictRecorder>(relaxed = true)
    private val syncSessionStore = mockk<SyncSessionStore>(relaxed = true)
    private val payloadParser = SyncPayloadParser()

    private lateinit var applier: ReplicaChangeApplier

    @Before
    fun setup() {
        applier = ReplicaChangeApplier(
            careReplicaRepository = careRepo,
            schedulingReplicaRepository = schedulingRepo,
            workflowReplicaRepository = workflowRepo,
            deviceReplicaRepository = deviceRepo,
            communicationReplicaRepository = commRepo,
            snapshotApplier = snapshotApplier,
            syncPayloadParser = payloadParser,
            conflictRecorder = conflictRecorder,
            syncSessionStore = syncSessionStore,
        )
    }

    private fun createOperation(
        aggregateReference: String,
        aggregateVersion: String,
        payloadType: String,
        payloadJson: String,
        operationType: SyncOperationType = SyncOperationType.DELTA,
    ) = SyncOperation(
        id = "op-1",
        operationType = operationType,
        aggregateReference = aggregateReference,
        aggregateVersion = aggregateVersion,
        payloadType = payloadType,
        payloadHash = "hash-1",
        payloadJson = payloadJson,
        status = "PENDING",
    )

    @Test
    fun applyNewMedicationCareDelta_appliesAllReplicasAndMarksDomains() = runTest {
        coEvery { careRepo.getCareActivityById("activity-1") } returns null
        coEvery { careRepo.getCareActivityByScheduleDefinition(any()) } returns null

        val payload = """
        {
            "care_activity_id": "activity-1",
            "elder_id": "elder-1",
            "activity_type": "MEDICATION",
            "status": "ACTIVE",
            "schedule_definition_id": "sched-1",
            "workflow_definition_id": "wf-1",
            "display_title": "Aspirin",
            "display_subtitle": "1 tablet",
            "schedule_definition": {
                "schedule_definition_id": "sched-1",
                "owner_reference": "activity-1",
                "recurrence_definition_json": "{}",
                "timezone": "UTC",
                "start_at_epoch_millis": 1000,
                "status": "ACTIVE"
            },
            "prescription": {
                "care_activity_id": "activity-1",
                "medication_reference": "aspirin",
                "dosage_information": "1 tablet",
                "elder_friendly_description": "Heart medication"
            },
            "occurrences": [
                {
                    "occurrence_id": "occ-1",
                    "schedule_definition_id": "sched-1",
                    "scheduled_for_epoch_millis": 2000,
                    "status": "SCHEDULED"
                }
            ]
        }
        """.trimIndent()

        val operation = createOperation(
            aggregateReference = "care_activity:activity-1",
            aggregateVersion = "1",
            payloadType = "care.activity.delta",
            payloadJson = payload,
        )

        val summary = applier.apply(listOf(operation))

        assertEquals(1, summary.appliedCount)
        assertEquals(0, summary.skippedCount)
        assertEquals(0, summary.conflictCount)
        assertTrue(summary.affectedReplicaDomains.contains(ReplicaDomain.CARE))
        assertTrue(summary.affectedReplicaDomains.contains(ReplicaDomain.SCHEDULING))

        coVerify { careRepo.upsertCareActivity(match { it.id == "activity-1" && it.status == "ACTIVE" }) }
        coVerify { careRepo.upsertPrescription(match { it.careActivityId == "activity-1" }) }
        coVerify { schedulingRepo.upsertScheduleDefinition(match { it.id == "sched-1" && it.status == "ACTIVE" }) }
        coVerify {
            schedulingRepo.replaceOccurrencesForSchedule(
                scheduleDefinitionId = "sched-1",
                occurrences = match { it.size == 1 && it[0].id == "occ-1" },
            )
        }
    }

    @Test
    fun applyCancelledSchedule_cancelsFutureOccurrencesInsteadOfReplacing() = runTest {
        coEvery { careRepo.getCareActivityById("activity-1") } returns null

        val payload = """
        {
            "care_activity_id": "activity-1",
            "elder_id": "elder-1",
            "activity_type": "MEDICATION",
            "status": "ACTIVE",
            "schedule_definition_id": "sched-1",
            "workflow_definition_id": "wf-1",
            "display_title": "Aspirin",
            "schedule_definition": {
                "schedule_definition_id": "sched-1",
                "owner_reference": "activity-1",
                "recurrence_definition_json": "{}",
                "timezone": "UTC",
                "start_at_epoch_millis": 1000,
                "status": "CANCELLED"
            }
        }
        """.trimIndent()

        val operation = createOperation(
            aggregateReference = "care_activity:activity-1",
            aggregateVersion = "2",
            payloadType = "care.activity.delta",
            payloadJson = payload,
        )

        val summary = applier.apply(listOf(operation))

        assertEquals(1, summary.appliedCount)
        coVerify { schedulingRepo.upsertScheduleDefinition(match { it.id == "sched-1" && it.status == "CANCELLED" }) }
        coVerify { schedulingRepo.cancelFutureOccurrencesForSchedule("sched-1", any()) }
        coVerify(exactly = 0) { schedulingRepo.replaceOccurrencesForSchedule(any(), any()) }
    }

    @Test
    fun applyEndedCareActivity_cancelsFutureOccurrences() = runTest {
        coEvery { careRepo.getCareActivityById("activity-1") } returns null

        val payload = """
        {
            "care_activity_id": "activity-1",
            "elder_id": "elder-1",
            "activity_type": "MEDICATION",
            "status": "ENDED",
            "schedule_definition_id": "sched-1",
            "workflow_definition_id": "wf-1",
            "display_title": "Aspirin"
        }
        """.trimIndent()

        val operation = createOperation(
            aggregateReference = "care_activity:activity-1",
            aggregateVersion = "3",
            payloadType = "care.activity.delta",
            payloadJson = payload,
        )

        val summary = applier.apply(listOf(operation))

        assertEquals(1, summary.appliedCount)
        coVerify { careRepo.upsertCareActivity(match { it.id == "activity-1" && it.status == "ENDED" }) }
        coVerify { schedulingRepo.cancelFutureOccurrencesForSchedule("sched-1", any()) }
    }

    @Test
    fun applyEqualVersion_isSkippedIdempotently() = runTest {
        val existingActivity = CareActivity(
            id = "activity-1",
            elderId = "elder-1",
            activityType = "MEDICATION",
            status = "ACTIVE",
            scheduleDefinitionId = "sched-1",
            workflowDefinitionId = "wf-1",
            displayTitle = "Aspirin",
            displaySubtitle = "",
            displayIcon = "",
            confirmationRequirementJson = "{}",
            compartmentAssignmentReference = "",
            aggregateVersion = 5L,
            updatedAtEpochMillis = 1000L,
        )
        coEvery { careRepo.getCareActivityById("activity-1") } returns existingActivity

        val payload = """
        {
            "care_activity_id": "activity-1",
            "elder_id": "elder-1",
            "activity_type": "MEDICATION",
            "status": "ACTIVE",
            "schedule_definition_id": "sched-1",
            "workflow_definition_id": "wf-1",
            "display_title": "Aspirin"
        }
        """.trimIndent()

        val operation = createOperation(
            aggregateReference = "care_activity:activity-1",
            aggregateVersion = "5",
            payloadType = "care.activity.delta",
            payloadJson = payload,
        )

        val summary = applier.apply(listOf(operation))

        assertEquals(0, summary.appliedCount)
        assertEquals(1, summary.skippedCount)
        assertEquals(0, summary.conflictCount)
        coVerify(exactly = 0) { careRepo.upsertCareActivity(any()) }
    }

    @Test
    fun applyOlderVersion_recordsConflictWithoutMutating() = runTest {
        val existingActivity = CareActivity(
            id = "activity-1",
            elderId = "elder-1",
            activityType = "MEDICATION",
            status = "ACTIVE",
            scheduleDefinitionId = "sched-1",
            workflowDefinitionId = "wf-1",
            displayTitle = "Aspirin",
            displaySubtitle = "",
            displayIcon = "",
            confirmationRequirementJson = "{}",
            compartmentAssignmentReference = "",
            aggregateVersion = 5L,
            updatedAtEpochMillis = 1000L,
        )
        coEvery { careRepo.getCareActivityById("activity-1") } returns existingActivity

        val payload = """
        {
            "care_activity_id": "activity-1",
            "elder_id": "elder-1",
            "activity_type": "MEDICATION",
            "status": "ACTIVE",
            "schedule_definition_id": "sched-1",
            "workflow_definition_id": "wf-1",
            "display_title": "Aspirin"
        }
        """.trimIndent()

        val operation = createOperation(
            aggregateReference = "care_activity:activity-1",
            aggregateVersion = "3",
            payloadType = "care.activity.delta",
            payloadJson = payload,
        )

        val summary = applier.apply(listOf(operation))

        assertEquals(0, summary.appliedCount)
        assertEquals(0, summary.skippedCount)
        assertEquals(1, summary.conflictCount)
        coVerify {
            conflictRecorder.recordVersionMismatch(
                aggregateReference = "care_activity:activity-1",
                localVersion = "5",
                remoteVersion = "3",
                sessionId = any(),
                payloadJson = payload,
            )
        }
        coVerify(exactly = 0) { careRepo.upsertCareActivity(any()) }
    }

    @Test
    fun applyContactDelta_upsertsContactAndMarksCommunicationDomain() = runTest {
        coEvery { commRepo.getContact("contact-1") } returns null

        val payload = """
        {
            "id": "contact-1",
            "elder_id": "elder-1",
            "display_name": "پسر",
            "phone": "+989121111111",
            "communication_identities_json": "[]",
            "preferred_channel": "VOICE",
            "photo_reference": null,
            "is_priority": true,
            "status": "ACTIVE",
            "updated_at_epoch_millis": 1000
        }
        """.trimIndent()

        val operation = createOperation(
            aggregateReference = "contact-1",
            aggregateVersion = "1000",
            payloadType = "communication.contact.delta",
            payloadJson = payload,
        )

        val summary = applier.apply(listOf(operation))

        assertEquals(1, summary.appliedCount)
        assertEquals(0, summary.skippedCount)
        assertEquals(0, summary.conflictCount)
        assertTrue(summary.affectedReplicaDomains.contains(ReplicaDomain.COMMUNICATION))
        coVerify(exactly = 1) { commRepo.upsertContact(match { it.id == "contact-1" && it.displayName == "پسر" }) }
    }
}
