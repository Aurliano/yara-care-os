package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.ReplicaSnapshotWriter
import ir.sayda.yara.hub.core.sync.ReplicaDomain
import ir.sayda.yara.hub.core.sync.SyncOperation
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SnapshotApplier @Inject constructor(
    private val replicaSnapshotWriter: ReplicaSnapshotWriter,
    private val syncPayloadParser: SyncPayloadParser,
) {
    suspend fun apply(operation: SyncOperation): Set<ReplicaDomain> {
        val bundle = syncPayloadParser.parseSnapshotBundle(operation.payloadJson)
        replicaSnapshotWriter.replaceReplicaTables(bundle)
        return buildSet {
            if (bundle.careActivities.isNotEmpty() || bundle.prescriptions.isNotEmpty()) add(ReplicaDomain.CARE)
            if (bundle.scheduleDefinitions.isNotEmpty() || bundle.occurrences.isNotEmpty()) add(ReplicaDomain.SCHEDULING)
            if (bundle.workflowDefinitions.isNotEmpty() || bundle.workflowExecutions.isNotEmpty()) add(ReplicaDomain.WORKFLOW)
            if (bundle.devices.isNotEmpty() || bundle.deviceCommands.isNotEmpty()) add(ReplicaDomain.DEVICE)
            if (bundle.communicationSessions.isNotEmpty() || bundle.contacts.isNotEmpty()) add(ReplicaDomain.COMMUNICATION)
        }
    }
}
