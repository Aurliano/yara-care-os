package ir.sayda.yara.hub.data.repository

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.PendingEvidence
import ir.sayda.yara.hub.core.domain.model.Prescription
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
import ir.sayda.yara.hub.core.domain.repository.ReminderRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.repository.RuntimeStateRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import java.util.Calendar
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConnectivityRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context,
) : ConnectivityRepository {

    override fun observeOnline(): Flow<Boolean> = flow {
        emit(isOnline())
    }.distinctUntilChanged()

    override suspend fun isOnline(): Boolean {
        val connectivityManager =
            context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }
}

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
    private val pendingEvidenceRepository: PendingEvidenceRepository,
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

        return combine(
            combine(
                workflowReplicaRepository.observeActiveExecutions(),
                schedulingReplicaRepository.observeOccurrencesDueBefore(endOfDay),
                careReplicaRepository.observeAllCareActivities(),
                careReplicaRepository.observePrescriptions(),
                replicaMetadataRepository.observeReplicaState(),
            ) { executions, dueOccurrences, careActivities, prescriptions, replicaState ->
                HomeReplicaInputs(
                    executions = executions,
                    dueOccurrences = dueOccurrences,
                    careActivities = careActivities,
                    prescriptions = prescriptions,
                    replicaState = replicaState,
                )
            },
            combine(
                runtimeStateRepository.observeKernelState(),
                connectivityRepository.observeOnline(),
                contactsFlow,
                pendingEvidenceRepository.observeHubConfirmationEvidence(),
            ) { kernelState, online, contacts, hubConfirmations ->
                HomeRuntimeInputs(
                    kernelState = kernelState,
                    online = online,
                    contacts = contacts,
                    hubConfirmations = hubConfirmations,
                )
            },
        ) { replicaInputs, runtimeInputs ->
            buildSnapshot(
                identity = identity,
                executions = replicaInputs.executions,
                dueOccurrences = replicaInputs.dueOccurrences,
                careActivities = replicaInputs.careActivities,
                prescriptions = replicaInputs.prescriptions,
                replicaState = replicaInputs.replicaState,
                runtimeHealth = runtimeInputs.kernelState?.lifecycleState ?: "UNKNOWN",
                online = runtimeInputs.online,
                contacts = runtimeInputs.contacts,
                locallyConfirmedExecutionIds = runtimeInputs.hubConfirmations
                    .map { it.workflowExecutionId }
                    .toSet(),
            )
        }
    }

    private data class HomeReplicaInputs(
        val executions: List<WorkflowExecution>,
        val dueOccurrences: List<Occurrence>,
        val careActivities: List<CareActivity>,
        val prescriptions: List<Prescription>,
        val replicaState: ReplicaState?,
    )

    private data class HomeRuntimeInputs(
        val kernelState: RuntimeStateRecord?,
        val online: Boolean,
        val contacts: List<Contact>,
        val hubConfirmations: List<PendingEvidence>,
    )

    private fun buildSnapshot(
        identity: HubIdentity?,
        executions: List<WorkflowExecution>,
        dueOccurrences: List<Occurrence>,
        careActivities: List<CareActivity>,
        prescriptions: List<Prescription>,
        replicaState: ReplicaState?,
        runtimeHealth: String,
        online: Boolean,
        contacts: List<Contact>,
        locallyConfirmedExecutionIds: Set<String>,
    ): HomeRuntimeSnapshot {
        val activityBySchedule = careActivities.associateBy { it.scheduleDefinitionId }
        val prescriptionByActivity = prescriptions.associateBy { it.careActivityId }
        val executionByOccurrence = executions.associateBy { it.occurrenceId }
        val todayReminders = dueOccurrences.map { occurrence ->
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
        return HomeRuntimeSnapshot(
            elderDisplayName = displayName,
            activeExecutions = executions,
            todayReminders = todayReminders,
            priorityContacts = contacts,
            replicaHealth = replicaState?.health ?: "UNKNOWN",
            runtimeHealth = runtimeHealth,
            lastSyncEpochMillis = replicaState?.lastSuccessfulSyncEpochMillis,
            isOnline = online,
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
        val localConfirmationRecorded =
            pendingEvidenceRepository.findHubConfirmationEvidence(executionId) != null
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
        )
    }
}
