package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.ConnectivityState
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.PendingEvidence
import ir.sayda.yara.hub.core.domain.model.Prescription
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.model.ReminderPresentation
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.domain.model.RuntimeStateRecord
import ir.sayda.yara.hub.core.domain.model.TodayReminderItem
import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.HomeRepository
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.domain.repository.ReminderRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.repository.RuntimeStateRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmRegistry
import ir.sayda.yara.hub.data.workflow.WorkflowPostponePolicyReader
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.delay
import java.util.Calendar
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HomeRepositoryImpl @Inject constructor(
    private val authRepository: AuthRepository,
    private val workflowReplicaRepository: WorkflowReplicaRepository,
    private val schedulingReplicaRepository: SchedulingReplicaRepository,
    private val careReplicaRepository: CareReplicaRepository,
    private val communicationReplicaRepository: CommunicationReplicaRepository,
    private val replicaMetadataRepository: ReplicaMetadataRepository,
    private val runtimeStateRepository: RuntimeStateRepository,
    private val connectivityRepository: ConnectivityRepository,
    private val provisioningRepository: ProvisioningRepository,
    private val pendingEvidenceRepository: PendingEvidenceRepository,
    private val occurrenceAlarmRegistry: OccurrenceAlarmRegistry,
    private val replicaDiagnosticsReader: ReplicaDiagnosticsReader,
) : HomeRepository {

    override fun observeHomeSnapshot(): Flow<HomeRuntimeSnapshot> =
        authRepository.observeIdentity().flatMapLatest { identity ->
            combineHomeSnapshot(identity)
        }

    private fun combineHomeSnapshot(identity: HubIdentity?): Flow<HomeRuntimeSnapshot> {
        val endOfDay = endOfTodayEpochMillis()
        val contactsFlow = identity?.elderId?.let { elderId ->
            communicationReplicaRepository.observePriorityContacts(elderId)
        } ?: flowOf(emptyList())

        return clockFlow().flatMapLatest { nowEpochMillis ->
            combine(
                combine(
                    workflowReplicaRepository.observeActiveExecutions(),
                    schedulingReplicaRepository.observeTodayReminders(endOfDay),
                    schedulingReplicaRepository.observeNextReminderOccurrence(nowEpochMillis, endOfDay),
                ) { executions, todayOccurrences, nextOccurrence ->
                    Triple(executions, todayOccurrences, nextOccurrence)
                },
            combine(
                careReplicaRepository.observeAllCareActivities(),
                careReplicaRepository.observePrescriptions(),
                replicaMetadataRepository.observeReplicaState(),
            ) { careActivities, prescriptions, replicaState ->
                Triple(careActivities, prescriptions, replicaState)
            },
            combine(
                combine(
                    runtimeStateRepository.observeKernelState(),
                    connectivityRepository.observeConnectivity(),
                    provisioningRepository.observeProvisioningStatus(),
                ) { kernelState, connectivity, provisioning ->
                    Triple(kernelState, connectivity, provisioning)
                },
                combine(
                    contactsFlow,
                    pendingEvidenceRepository.observeHubConfirmationEvidence(),
                    pendingEvidenceRepository.observePendingCount(),
                ) { contacts, hubConfirmations, pendingEvidenceCount ->
                    Triple(contacts, hubConfirmations, pendingEvidenceCount)
                },
            ) { runtimeTriple, evidenceTriple ->
                HomeRuntimeInputs(
                    kernelState = runtimeTriple.first,
                    connectivity = runtimeTriple.second,
                    provisioning = runtimeTriple.third,
                    contacts = evidenceTriple.first,
                    hubConfirmations = evidenceTriple.second,
                    pendingEvidenceCount = evidenceTriple.third,
                )
            },
            replicaDiagnosticsReader.observeCounts(),
            ) { executionInputs, careInputs, runtimeInputs, diagnostics ->
                val (executions, todayOccurrences, nextOccurrence) = executionInputs
                val (careActivities, prescriptions, replicaState) = careInputs
                buildSnapshot(
                    identity = identity,
                    executions = executions,
                    todayOccurrences = todayOccurrences,
                    nextOccurrence = nextOccurrence,
                    careActivities = careActivities,
                    prescriptions = prescriptions,
                    replicaState = replicaState,
                    runtimeHealth = runtimeInputs.kernelState?.lifecycleState ?: "UNKNOWN",
                    online = runtimeInputs.connectivity.state != ConnectivityState.DISCONNECTED,
                    contacts = runtimeInputs.contacts,
                    pendingEvidenceCount = runtimeInputs.pendingEvidenceCount,
                    registeredAlarmCount = occurrenceAlarmRegistry.queryRegisteredOccurrenceIds().size,
                    locallyConfirmedExecutionIds = runtimeInputs.hubConfirmations
                        .map { it.workflowExecutionId }
                        .toSet(),
                    provisioning = runtimeInputs.provisioning,
                    connectivity = runtimeInputs.connectivity,
                    diagnostics = diagnostics,
                )
            }
        }
    }

    private fun clockFlow(intervalMs: Long = 15_000L): Flow<Long> = flow {
        while (true) {
            emit(System.currentTimeMillis())
            delay(intervalMs)
        }
    }.onStart { emit(System.currentTimeMillis()) }

    private data class HomeRuntimeInputs(
        val kernelState: RuntimeStateRecord?,
        val connectivity: ir.sayda.yara.hub.core.domain.model.ConnectivitySnapshot,
        val provisioning: ir.sayda.yara.hub.core.domain.model.ProvisioningStatus,
        val contacts: List<Contact>,
        val hubConfirmations: List<PendingEvidence>,
        val pendingEvidenceCount: Int,
    )

    private fun buildSnapshot(
        identity: HubIdentity?,
        executions: List<WorkflowExecution>,
        todayOccurrences: List<Occurrence>,
        nextOccurrence: Occurrence?,
        careActivities: List<CareActivity>,
        prescriptions: List<Prescription>,
        replicaState: ReplicaState?,
        runtimeHealth: String,
        online: Boolean,
        contacts: List<Contact>,
        pendingEvidenceCount: Int,
        registeredAlarmCount: Int,
        locallyConfirmedExecutionIds: Set<String>,
        provisioning: ir.sayda.yara.hub.core.domain.model.ProvisioningStatus,
        connectivity: ir.sayda.yara.hub.core.domain.model.ConnectivitySnapshot,
        diagnostics: ReplicaTableCounts,
    ): HomeRuntimeSnapshot {
        val activityBySchedule = careActivities.associateBy { it.scheduleDefinitionId }
        val prescriptionByActivity = prescriptions.associateBy { it.careActivityId }
        val executionByOccurrence = executions.associateBy { it.occurrenceId }
        val todayReminders = todayOccurrences.map { occurrence ->
            val activity = activityBySchedule[occurrence.scheduleDefinitionId]
            val prescription = activity?.let { prescriptionByActivity[it.id] }
            TodayReminderItem(
                occurrenceId = occurrence.id,
                executionId = executionByOccurrence[occurrence.id]?.id,
                title = activity?.displayTitle ?: "یادآور",
                friendlyDescription = prescription?.elderFriendlyDescription
                    ?: activity?.displaySubtitle
                    ?: "",
                scheduledForEpochMillis = occurrence.scheduledForEpochMillis,
                status = occurrence.status,
                localConfirmationRecorded = executionByOccurrence[occurrence.id]?.id
                    ?.let { locallyConfirmedExecutionIds.contains(it) }
                    ?: false,
            )
        }
        val displayName = careActivities.firstOrNull { it.elderId == identity?.elderId }?.displayTitle
            ?: identity?.elderId
            ?: "سالمند"
        val nextActivity = nextOccurrence?.let { activityBySchedule[it.scheduleDefinitionId] }
        return HomeRuntimeSnapshot(
            elderDisplayName = displayName,
            activeExecutions = executions,
            todayReminders = todayReminders,
            priorityContacts = contacts,
            replicaHealth = replicaState?.health ?: "UNKNOWN",
            runtimeHealth = runtimeHealth,
            lastSyncEpochMillis = replicaState?.lastSuccessfulSyncEpochMillis,
            isOnline = online,
            nextReminderEpochMillis = nextOccurrence?.scheduledForEpochMillis,
            nextReminderTitle = nextActivity?.displayTitle,
            pendingEvidenceCount = pendingEvidenceCount,
            synchronizationAvailable = online && provisioning.state == ProvisioningState.READY,
            registeredAlarmCount = registeredAlarmCount,
            provisioningState = provisioning.state,
            connectivityState = connectivity.state,
            deviceId = identity?.deviceId ?: provisioning.deviceId,
            replicaId = identity?.replicaId ?: provisioning.replicaId,
            backendUrl = identity?.backendUrl ?: provisioning.backendUrl,
            tokenExpiresAtEpochMillis = identity?.tokenExpiresAtEpochMillis,
            lastAuthenticatedAtEpochMillis = identity?.lastAuthenticatedAtEpochMillis
                ?: provisioning.lastAuthenticatedAtEpochMillis,
            isAuthenticated = identity != null &&
                identity.provisioningState == ProvisioningState.READY &&
                identity.accessToken.isNotBlank(),
            connectionType = connectivity.connectionType,
            checkpointSequence = replicaState?.checkpointSequence ?: 0L,
            lastDownloadSessionId = diagnostics.lastDownloadSessionId,
            careActivityCount = diagnostics.careActivityCount,
            workflowDefinitionCount = diagnostics.workflowDefinitionCount,
            workflowExecutionCount = diagnostics.workflowExecutionCount,
            scheduleDefinitionCount = diagnostics.scheduleDefinitionCount,
            occurrenceCount = diagnostics.occurrenceCount,
            deviceCount = diagnostics.deviceCount,
            deviceCommandCount = diagnostics.deviceCommandCount,
            communicationSessionCount = diagnostics.communicationSessionCount,
            contactCount = diagnostics.contactCount,
            outboxPendingCount = diagnostics.outboxPendingCount,
            syncConflictCount = diagnostics.syncConflictCount,
            lastProvisioningError = provisioning.lastErrorMessage,
        )
    }

    private fun endOfTodayEpochMillis(): Long {
        val calendar = Calendar.getInstance()
        calendar.set(Calendar.HOUR_OF_DAY, 23)
        calendar.set(Calendar.MINUTE, 59)
        calendar.set(Calendar.SECOND, 59)
        calendar.set(Calendar.MILLISECOND, 999)
        return calendar.timeInMillis
    }
}

@Singleton
class ReminderRepositoryImpl @Inject constructor(
    private val workflowReplicaRepository: WorkflowReplicaRepository,
    private val schedulingReplicaRepository: SchedulingReplicaRepository,
    private val careReplicaRepository: CareReplicaRepository,
    private val pendingEvidenceRepository: PendingEvidenceRepository,
) : ReminderRepository {

    override suspend fun loadPresentation(executionId: String): ReminderPresentation? {
        val execution = workflowReplicaRepository.getExecution(executionId) ?: return null
        val occurrence = schedulingReplicaRepository.getOccurrence(execution.occurrenceId) ?: return null
        val activity = careReplicaRepository.getCareActivityByScheduleDefinition(occurrence.scheduleDefinitionId)
        val prescription = activity?.let { careReplicaRepository.getPrescription(it.id) }
        val definition = activity?.let { workflowReplicaRepository.getDefinition(it.workflowDefinitionId) }
        val postponePolicy = definition?.let { WorkflowPostponePolicyReader.read(it.definitionJson) }
        val localConfirmationRecorded =
            pendingEvidenceRepository.findHubConfirmationEvidence(executionId) != null
        val remainingPostpones = postponePolicy?.let { policy ->
            (policy.maxCount - execution.postponeCount).coerceAtLeast(0)
        } ?: 0
        return ReminderPresentation(
            executionId = execution.id,
            occurrenceId = occurrence.id,
            title = activity?.displayTitle ?: "یادآور دارو",
            friendlyDescription = prescription?.elderFriendlyDescription
                ?: activity?.displaySubtitle
                ?: "لطفاً داروی خود را مصرف کنید.",
            scheduledForEpochMillis = occurrence.scheduledForEpochMillis,
            workflowStatus = execution.status,
            localConfirmationRecorded = localConfirmationRecorded,
            postponeAllowed = postponePolicy?.allowed == true && remainingPostpones > 0,
            remainingPostpones = remainingPostpones,
            postponeDelayMinutes = postponePolicy?.delaySeconds?.let { (it / 60).toInt().coerceAtLeast(1) } ?: 0,
        )
    }
}
