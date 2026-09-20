package ir.sayda.yara.hub.data.repository

import io.mockk.every
import io.mockk.mockk
import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.ConnectivitySnapshot
import ir.sayda.yara.hub.core.domain.model.ConnectivityState
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.model.ProvisioningStatus
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.domain.model.RuntimeStateRecord
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.repository.RuntimeStateRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmRegistry
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Before
import org.junit.Test

class HomeRepositoryGreetingTest {

    private val authRepository: AuthRepository = mockk(relaxed = true)
    private val workflowReplicaRepository: WorkflowReplicaRepository = mockk(relaxed = true)
    private val schedulingReplicaRepository: SchedulingReplicaRepository = mockk(relaxed = true)
    private val careReplicaRepository: CareReplicaRepository = mockk(relaxed = true)
    private val communicationReplicaRepository: CommunicationReplicaRepository = mockk(relaxed = true)
    private val replicaMetadataRepository: ReplicaMetadataRepository = mockk(relaxed = true)
    private val runtimeStateRepository: RuntimeStateRepository = mockk(relaxed = true)
    private val connectivityRepository: ConnectivityRepository = mockk(relaxed = true)
    private val provisioningRepository: ProvisioningRepository = mockk(relaxed = true)
    private val pendingEvidenceRepository: PendingEvidenceRepository = mockk(relaxed = true)
    private val occurrenceAlarmRegistry: OccurrenceAlarmRegistry = mockk(relaxed = true)
    private val replicaDiagnosticsReader: ReplicaDiagnosticsReader = mockk(relaxed = true)

    private lateinit var homeRepository: HomeRepositoryImpl

    private fun createCareActivity(id: String, title: String) = CareActivity(
        id = id,
        elderId = "elder-123",
        activityType = "MEDICATION",
        status = "ACTIVE",
        scheduleDefinitionId = "sched-$id",
        workflowDefinitionId = "wf-$id",
        displayTitle = title,
        displaySubtitle = "Take 1 tablet after dinner",
        displayIcon = "pill",
        confirmationRequirementJson = "{}",
        compartmentAssignmentReference = "comp-1",
        aggregateVersion = 1L,
        updatedAtEpochMillis = 1000L,
    )

    private val medicationActivity1 = createCareActivity("act-1", "Evening Calcium")
    private val medicationActivity2 = createCareActivity("act-2", "Morning Aspirin")

    @Before
    fun setup() {
        val replicaState = ReplicaState(
            replicaIdentifier = "rep-1",
            replicaType = "HUB",
            health = "HEALTHY",
            status = "SYNCED",
            checkpointSequence = 1L,
            checkpointToken = null,
            lastSuccessfulSyncEpochMillis = 1000L,
        )
        val runtimeRecord = RuntimeStateRecord(
            componentId = "KERNEL",
            lifecycleState = "RUNNING",
            statePayloadJson = "{}",
            updatedAtEpochMillis = 1000L,
        )
        val connectivity = ConnectivitySnapshot(
            state = ConnectivityState.CONNECTED,
            connectionType = "WIFI",
            isBackendReachable = true,
        )

        every { workflowReplicaRepository.observeActiveExecutions() } returns flowOf(emptyList())
        every { schedulingReplicaRepository.observeTodayReminders(any(), any()) } returns flowOf(emptyList())
        every { schedulingReplicaRepository.observeNextScheduledOccurrence(any()) } returns flowOf(null)
        every { careReplicaRepository.observePrescriptions() } returns flowOf(emptyList())
        every { replicaMetadataRepository.observeReplicaState() } returns flowOf(replicaState)
        every { runtimeStateRepository.observeKernelState() } returns flowOf(runtimeRecord)
        every { connectivityRepository.observeConnectivity() } returns flowOf(connectivity)
        every { provisioningRepository.observeProvisioningStatus() } returns flowOf(ProvisioningStatus(state = ProvisioningState.READY, deviceId = "dev-1"))
        every { pendingEvidenceRepository.observeHubConfirmationEvidence() } returns flowOf(emptyList())
        every { pendingEvidenceRepository.observePendingCount() } returns flowOf(0)
        every { communicationReplicaRepository.observePriorityContacts(any()) } returns flowOf(emptyList())
        every { communicationReplicaRepository.observeContacts(any()) } returns flowOf(emptyList())
        every { replicaDiagnosticsReader.observeCounts() } returns flowOf(ReplicaTableCounts())

        homeRepository = HomeRepositoryImpl(
            authRepository = authRepository,
            workflowReplicaRepository = workflowReplicaRepository,
            schedulingReplicaRepository = schedulingReplicaRepository,
            careReplicaRepository = careReplicaRepository,
            communicationReplicaRepository = communicationReplicaRepository,
            replicaMetadataRepository = replicaMetadataRepository,
            runtimeStateRepository = runtimeStateRepository,
            connectivityRepository = connectivityRepository,
            provisioningRepository = provisioningRepository,
            pendingEvidenceRepository = pendingEvidenceRepository,
            occurrenceAlarmRegistry = occurrenceAlarmRegistry,
            replicaDiagnosticsReader = replicaDiagnosticsReader,
        )
    }

    @Test
    fun elderGreeting_usesElderDisplayName_whenPresent() = runBlocking {
        val identity = HubIdentity(
            deviceId = "dev-1",
            replicaId = "rep-1",
            elderId = "elder-123",
            accessToken = "token",
            refreshToken = "refresh",
            tokenExpiresAtEpochMillis = 9999999L,
            backendUrl = "http://test",
            provisionedAtEpochMillis = 1000L,
            lastAuthenticatedAtEpochMillis = 1000L,
            provisioningState = ProvisioningState.READY,
            elderDisplayName = "مامان پروانه",
        )
        every { authRepository.observeIdentity() } returns flowOf(identity)
        every { careReplicaRepository.observeAllCareActivities() } returns flowOf(listOf(medicationActivity1, medicationActivity2))

        val snapshot = homeRepository.observeHomeSnapshot().first()

        assertEquals("مامان پروانه", snapshot.elderDisplayName)
        assertNotEquals("Evening Calcium", snapshot.elderDisplayName)
        assertNotEquals("Morning Aspirin", snapshot.elderDisplayName)
    }

    @Test
    fun elderGreeting_fallsBackToGenericElder_whenElderDisplayNameMissing() = runBlocking {
        val identity = HubIdentity(
            deviceId = "dev-1",
            replicaId = "rep-1",
            elderId = "elder-123",
            accessToken = "token",
            refreshToken = "refresh",
            tokenExpiresAtEpochMillis = 9999999L,
            backendUrl = "http://test",
            provisionedAtEpochMillis = 1000L,
            lastAuthenticatedAtEpochMillis = 1000L,
            provisioningState = ProvisioningState.READY,
            elderDisplayName = null,
        )
        every { authRepository.observeIdentity() } returns flowOf(identity)
        every { careReplicaRepository.observeAllCareActivities() } returns flowOf(listOf(medicationActivity1, medicationActivity2))

        val snapshot = homeRepository.observeHomeSnapshot().first()

        assertEquals("سالمند", snapshot.elderDisplayName)
        assertNotEquals("Evening Calcium", snapshot.elderDisplayName)
        assertNotEquals("Morning Aspirin", snapshot.elderDisplayName)
    }

    @Test
    fun elderGreeting_neverPollutesWithCareActivityTitle_evenIfMedicationMatchesElderId() = runBlocking {
        val identity = HubIdentity(
            deviceId = "dev-1",
            replicaId = "rep-1",
            elderId = "elder-123",
            accessToken = "token",
            refreshToken = "refresh",
            tokenExpiresAtEpochMillis = 9999999L,
            backendUrl = "http://test",
            provisionedAtEpochMillis = 1000L,
            lastAuthenticatedAtEpochMillis = 1000L,
            provisioningState = ProvisioningState.READY,
            elderDisplayName = "بابا احمد",
        )
        every { authRepository.observeIdentity() } returns flowOf(identity)
        every { careReplicaRepository.observeAllCareActivities() } returns flowOf(listOf(medicationActivity1))

        val snapshot = homeRepository.observeHomeSnapshot().first()

        assertEquals("بابا احمد", snapshot.elderDisplayName)
        assertNotEquals("Evening Calcium", snapshot.elderDisplayName)
    }
}
