package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.DeviceReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.sync.ApplySummary
import ir.sayda.yara.hub.core.sync.ReplicaDomain
import ir.sayda.yara.hub.core.sync.SyncOperation
import ir.sayda.yara.hub.core.sync.SyncOperationType
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ReplicaChangeApplier @Inject constructor(
    private val careReplicaRepository: CareReplicaRepository,
    private val schedulingReplicaRepository: SchedulingReplicaRepository,
    private val workflowReplicaRepository: WorkflowReplicaRepository,
    private val deviceReplicaRepository: DeviceReplicaRepository,
    private val communicationReplicaRepository: CommunicationReplicaRepository,
    private val snapshotApplier: SnapshotApplier,
    private val syncPayloadParser: SyncPayloadParser,
    private val conflictRecorder: ConflictRecorder,
    private val syncSessionStore: SyncSessionStore,
) {
    suspend fun apply(operations: List<SyncOperation>): ApplySummary {
        var applied = 0
        var skipped = 0
        var conflicts = 0
        val domains = mutableSetOf<ReplicaDomain>()
        val confirmedExecutions = mutableSetOf<String>()

        for (operation in operations) {
            if (operation.operationType == SyncOperationType.SNAPSHOT || operation.payloadType.endsWith(".snapshot")) {
                domains += snapshotApplier.apply(operation)
                applied++
                continue
            }

            when (operation.payloadType) {
                "care.activity.delta" -> when (applyCareDelta(operation)) {
                    ApplyOutcome.APPLIED -> {
                        applied++
                        domains += ReplicaDomain.CARE
                        if (syncPayloadParser.careDeltaIncludesScheduling(operation.payloadJson)) {
                            domains += ReplicaDomain.SCHEDULING
                        }
                    }
                    ApplyOutcome.SKIPPED -> skipped++
                    ApplyOutcome.CONFLICT -> conflicts++
                }
                "workflow.execution.delta" -> when (applyWorkflowDelta(operation)) {
                    ApplyOutcome.APPLIED -> {
                        applied++
                        domains += ReplicaDomain.WORKFLOW
                        val execution = syncPayloadParser.parseWorkflowExecution(
                            operation.payloadJson,
                            operation.aggregateVersion,
                        )
                        if (execution.status == "CONFIRMED") {
                            confirmedExecutions += execution.id
                        }
                    }
                    ApplyOutcome.SKIPPED -> skipped++
                    ApplyOutcome.CONFLICT -> conflicts++
                }
                "device.delta" -> when (applyDeviceDelta(operation)) {
                    ApplyOutcome.APPLIED -> {
                        applied++
                        domains += ReplicaDomain.DEVICE
                    }
                    ApplyOutcome.SKIPPED -> skipped++
                    ApplyOutcome.CONFLICT -> conflicts++
                }
                "communication.session.delta" -> when (applyCommunicationDelta(operation)) {
                    ApplyOutcome.APPLIED -> {
                        applied++
                        domains += ReplicaDomain.COMMUNICATION
                    }
                    ApplyOutcome.SKIPPED -> skipped++
                    ApplyOutcome.CONFLICT -> conflicts++
                }
                else -> skipped++
            }
        }

        return ApplySummary(
            appliedCount = applied,
            skippedCount = skipped,
            conflictCount = conflicts,
            affectedReplicaDomains = domains,
            confirmedExecutionIds = confirmedExecutions,
        )
    }

    private enum class ApplyOutcome { APPLIED, SKIPPED, CONFLICT }

    private suspend fun applyCareDelta(operation: SyncOperation): ApplyOutcome {
        val bundle = syncPayloadParser.parseCareActivityBundle(operation.payloadJson, operation.aggregateVersion)
        val current = careReplicaRepository.getCareActivityByScheduleDefinition(bundle.activity.scheduleDefinitionId)
        return applyWithVersionGuard(
            operation = operation,
            localVersion = current?.aggregateVersion?.toString(),
        ) {
            careReplicaRepository.upsertCareActivity(bundle.activity)
            val schedule = bundle.schedule
            if (schedule != null) {
                schedulingReplicaRepository.upsertScheduleDefinition(schedule)
                schedulingReplicaRepository.replaceOccurrencesForSchedule(
                    scheduleDefinitionId = schedule.id,
                    occurrences = bundle.occurrences,
                )
            }
        }
    }

    private suspend fun applyWorkflowDelta(operation: SyncOperation): ApplyOutcome {
        val execution = syncPayloadParser.parseWorkflowExecution(operation.payloadJson, operation.aggregateVersion)
        val current = workflowReplicaRepository.getExecution(execution.id)
        return applyWithVersionGuard(
            operation = operation,
            localVersion = current?.aggregateVersion?.toString(),
        ) {
            workflowReplicaRepository.upsertExecution(execution)
        }
    }

    private suspend fun applyDeviceDelta(operation: SyncOperation): ApplyOutcome {
        val device = syncPayloadParser.parseDevice(operation.payloadJson, operation.aggregateVersion)
        return applyWithVersionGuard(operation, null) {
            deviceReplicaRepository.upsertDevice(device)
        }
    }

    private suspend fun applyCommunicationDelta(operation: SyncOperation): ApplyOutcome {
        val session = syncPayloadParser.parseCommunicationSession(operation.payloadJson, operation.aggregateVersion)
        return applyWithVersionGuard(operation, null) {
            communicationReplicaRepository.upsertSession(session)
        }
    }

    private suspend fun applyWithVersionGuard(
        operation: SyncOperation,
        localVersion: String?,
        upsert: suspend () -> Unit,
    ): ApplyOutcome {
        when (AggregateVersionGuard.compare(operation.aggregateVersion, localVersion)) {
            VersionComparison.EQUAL -> return ApplyOutcome.SKIPPED
            VersionComparison.INCOMING_OLDER -> {
                conflictRecorder.recordVersionMismatch(
                    aggregateReference = operation.aggregateReference,
                    localVersion = localVersion,
                    remoteVersion = operation.aggregateVersion,
                    sessionId = syncSessionStore.getCached()?.sessionId,
                    payloadJson = operation.payloadJson,
                )
                return ApplyOutcome.CONFLICT
            }
            VersionComparison.INCOMING_NEWER, VersionComparison.NO_LOCAL -> {
                upsert()
                return ApplyOutcome.APPLIED
            }
        }
    }
}
