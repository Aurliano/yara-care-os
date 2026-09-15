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
            runCatching {
                android.util.Log.i("YaraSync", "replica.operation.received aggregate=${operation.aggregateReference} type=${operation.payloadType} version=${operation.aggregateVersion}")
            }
            if (operation.operationType == SyncOperationType.SNAPSHOT || operation.payloadType.endsWith(".snapshot")) {
                domains += snapshotApplier.apply(operation)
                applied++
                runCatching {
                    android.util.Log.i("YaraSync", "replica.operation.applied aggregate=${operation.aggregateReference} type=snapshot")
                }
                continue
            }

            when (operation.payloadType) {
                "care.activity.delta" -> when (applyCareDelta(operation)) {
                    ApplyOutcome.APPLIED -> {
                        applied++
                        domains += ReplicaDomain.CARE
                        domains += ReplicaDomain.SCHEDULING
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.applied aggregate=${operation.aggregateReference} type=${operation.payloadType}")
                        }
                    }
                    ApplyOutcome.SKIPPED -> {
                        skipped++
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.skipped aggregate=${operation.aggregateReference} reason=version_guard")
                        }
                    }
                    ApplyOutcome.CONFLICT -> {
                        conflicts++
                        runCatching {
                            android.util.Log.w("YaraSync", "replica.operation.conflict aggregate=${operation.aggregateReference} version=${operation.aggregateVersion}")
                        }
                    }
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
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.applied aggregate=${operation.aggregateReference} type=${operation.payloadType}")
                        }
                    }
                    ApplyOutcome.SKIPPED -> {
                        skipped++
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.skipped aggregate=${operation.aggregateReference} reason=version_guard")
                        }
                    }
                    ApplyOutcome.CONFLICT -> {
                        conflicts++
                        runCatching {
                            android.util.Log.w("YaraSync", "replica.operation.conflict aggregate=${operation.aggregateReference} version=${operation.aggregateVersion}")
                        }
                    }
                }
                "device.delta" -> when (applyDeviceDelta(operation)) {
                    ApplyOutcome.APPLIED -> {
                        applied++
                        domains += ReplicaDomain.DEVICE
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.applied aggregate=${operation.aggregateReference} type=${operation.payloadType}")
                        }
                    }
                    ApplyOutcome.SKIPPED -> {
                        skipped++
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.skipped aggregate=${operation.aggregateReference} reason=version_guard")
                        }
                    }
                    ApplyOutcome.CONFLICT -> {
                        conflicts++
                        runCatching {
                            android.util.Log.w("YaraSync", "replica.operation.conflict aggregate=${operation.aggregateReference} version=${operation.aggregateVersion}")
                        }
                    }
                }
                "communication.session.delta" -> when (applyCommunicationDelta(operation)) {
                    ApplyOutcome.APPLIED -> {
                        applied++
                        domains += ReplicaDomain.COMMUNICATION
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.applied aggregate=${operation.aggregateReference} type=${operation.payloadType}")
                        }
                    }
                    ApplyOutcome.SKIPPED -> {
                        skipped++
                        runCatching {
                            android.util.Log.i("YaraSync", "replica.operation.skipped aggregate=${operation.aggregateReference} reason=version_guard")
                        }
                    }
                    ApplyOutcome.CONFLICT -> {
                        conflicts++
                        runCatching {
                            android.util.Log.w("YaraSync", "replica.operation.conflict aggregate=${operation.aggregateReference} version=${operation.aggregateVersion}")
                        }
                    }
                }
                else -> {
                    skipped++
                    runCatching {
                        android.util.Log.w("YaraSync", "replica.operation.skipped aggregate=${operation.aggregateReference} reason=unknown_payload_type type=${operation.payloadType}")
                    }
                }
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
        val current = careReplicaRepository.getCareActivityById(bundle.activity.id)
            ?: careReplicaRepository.getCareActivityByScheduleDefinition(bundle.activity.scheduleDefinitionId)
        return applyWithVersionGuard(
            operation = operation,
            localVersion = current?.aggregateVersion?.toString(),
        ) {
            careReplicaRepository.upsertCareActivity(bundle.activity)
            bundle.prescription?.let { careReplicaRepository.upsertPrescription(it) }
            val schedule = bundle.schedule
            val isCareEnded = bundle.activity.status.equals("ENDED", ignoreCase = true) ||
                              bundle.activity.status.equals("CANCELLED", ignoreCase = true)
            val isScheduleEnded = schedule?.status?.equals("CANCELLED", ignoreCase = true) == true ||
                                  schedule?.status?.equals("ENDED", ignoreCase = true) == true

            if (schedule != null) {
                schedulingReplicaRepository.upsertScheduleDefinition(schedule)
                if (isCareEnded || isScheduleEnded) {
                    schedulingReplicaRepository.cancelFutureOccurrencesForSchedule(schedule.id)
                } else {
                    schedulingReplicaRepository.replaceOccurrencesForSchedule(
                        scheduleDefinitionId = schedule.id,
                        occurrences = bundle.occurrences,
                    )
                }
            } else if (isCareEnded && bundle.activity.scheduleDefinitionId.isNotBlank()) {
                schedulingReplicaRepository.cancelFutureOccurrencesForSchedule(bundle.activity.scheduleDefinitionId)
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
