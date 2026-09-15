import re

file_path = r"c:\yara-care-os\apps\hub\data\src\main\java\ir\sayda\yara\hub\data\repository\HomeAndConnectivityRepositories.kt"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the observeNextReminderOccurrence with flowOf(null) and remove the flatMapLatest
new_content = content.replace(
"""        return clockFlow().flatMapLatest { nowEpochMillis ->
            combine(
                combine(
                    workflowReplicaRepository.observeActiveExecutions(),
                    schedulingReplicaRepository.observeTodayReminders(endOfDay),
                    schedulingReplicaRepository.observeNextReminderOccurrence(nowEpochMillis, endOfDay),
                ) { executions, todayOccurrences, nextOccurrence ->
                    Triple(executions, todayOccurrences, nextOccurrence)
                },""",
"""        return combine(
            clockFlow(),
            combine(
                workflowReplicaRepository.observeActiveExecutions(),
                schedulingReplicaRepository.observeTodayReminders(endOfDay),
                kotlinx.coroutines.flow.flowOf(null as ir.sayda.yara.hub.core.domain.model.Occurrence?)
            ) { executions, todayOccurrences, nextOccurrence ->
                Triple(executions, todayOccurrences, nextOccurrence)
            },"""
)

# Now fix the end of the combine where it takes the block arguments
new_content = new_content.replace(
"""            ) { runtimeTriple, evidenceTriple ->
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
                    nowEpochMillis = nowEpochMillis,
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
                    confirmedAtByExecutionId = runtimeInputs.hubConfirmations
                        .groupBy { it.workflowExecutionId }
                        .mapValues { it.value.maxOf { c -> c.timestampEpochMillis } },
                    provisioning = runtimeInputs.provisioning,
                    connectivity = runtimeInputs.connectivity,
                    diagnostics = diagnostics,
                )
            }
        }""",
"""            ) { runtimeTriple, evidenceTriple ->
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
            ) { nowEpochMillis, executionInputs, careInputs, runtimeInputs, diagnostics ->
                val (executions, todayOccurrences, _) = executionInputs
                val (careActivities, prescriptions, replicaState) = careInputs
                val nextOccurrence = todayOccurrences
                    .filter { it.scheduledForEpochMillis > nowEpochMillis && it.status.name == "SCHEDULED" }
                    .minByOrNull { it.scheduledForEpochMillis }
                buildSnapshot(
                    identity = identity,
                    nowEpochMillis = nowEpochMillis,
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
                    confirmedAtByExecutionId = runtimeInputs.hubConfirmations
                        .groupBy { it.workflowExecutionId }
                        .mapValues { it.value.maxOf { c -> c.timestampEpochMillis } },
                    provisioning = runtimeInputs.provisioning,
                    connectivity = runtimeInputs.connectivity,
                    diagnostics = diagnostics,
                )
            }"""
)

# And finally fix the buildSnapshot mapping
build_snapshot_search = """        val allTodayReminders = todayOccurrences.map { occurrence ->
            val activity = activityBySchedule[occurrence.scheduleDefinitionId]
            val prescription = activity?.let { prescriptionByActivity[it.id] }
            val confirmedAt = executionByOccurrence[occurrence.id]?.id?.let { confirmedAtByExecutionId[it] }
            TodayReminderItem(
                occurrenceId = occurrence.id,
                executionId = executionByOccurrence[occurrence.id]?.id,
                title = activity?.displayTitle ?: "یادآوری",
                friendlyDescription = prescription?.elderFriendlyDescription
                    ?: activity?.displayTitle ?: "وقت خوردن دارو است.",
                scheduledForEpochMillis = occurrence.scheduledForEpochMillis,
                status = occurrence.status.name,
                confirmedAtEpochMillis = confirmedAt,
            )
        }"""

build_snapshot_replace = """        val allTodayReminders = todayOccurrences.mapNotNull { occurrence ->
            val activity = activityBySchedule[occurrence.scheduleDefinitionId]
            if (activity == null || activity.status != "ACTIVE") {
                return@mapNotNull null
            }
            val prescription = prescriptionByActivity[activity.id]
            val confirmedAt = executionByOccurrence[occurrence.id]?.id?.let { confirmedAtByExecutionId[it] }
            TodayReminderItem(
                occurrenceId = occurrence.id,
                executionId = executionByOccurrence[occurrence.id]?.id,
                title = activity.displayTitle,
                friendlyDescription = prescription?.elderFriendlyDescription
                    ?: activity.displayTitle,
                scheduledForEpochMillis = occurrence.scheduledForEpochMillis,
                status = occurrence.status.name,
                confirmedAtEpochMillis = confirmedAt,
            )
        }"""

new_content = new_content.replace(build_snapshot_search, build_snapshot_replace)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("SUCCESS")
