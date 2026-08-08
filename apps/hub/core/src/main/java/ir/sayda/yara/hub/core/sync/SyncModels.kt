package ir.sayda.yara.hub.core.sync

enum class SyncOperationType {
    DELTA,
    SNAPSHOT,
}

enum class ConflictType {
    VERSION_MISMATCH,
    CHECKPOINT_MISMATCH,
    CONCURRENT_CHANGE,
}

enum class ReplicaDomain {
    CARE,
    SCHEDULING,
    WORKFLOW,
    DEVICE,
    COMMUNICATION,
}

data class SyncOperation(
    val id: String,
    val operationType: SyncOperationType,
    val aggregateReference: String,
    val aggregateVersion: String,
    val payloadType: String,
    val payloadHash: String,
    val payloadJson: String,
    val status: String,
)

data class SyncConflictRecord(
    val id: String,
    val aggregateReference: String,
    val conflictType: ConflictType,
    val localVersion: String?,
    val remoteVersion: String?,
    val sessionId: String?,
    val detectedAtEpochMillis: Long,
    val payloadJson: String,
)

data class ApplySummary(
    val appliedCount: Int,
    val skippedCount: Int,
    val conflictCount: Int,
    val affectedReplicaDomains: Set<ReplicaDomain>,
    val confirmedExecutionIds: Set<String> = emptySet(),
) {
    val hasAppliedChanges: Boolean get() = appliedCount > 0
}

data class SyncRefreshScope(
    val scheduling: Boolean = false,
    val workflow: Boolean = false,
    val care: Boolean = false,
    val device: Boolean = false,
    val communication: Boolean = false,
) {
    val isEmpty: Boolean get() = !scheduling && !workflow && !care && !device && !communication

    companion object {
        fun full(): SyncRefreshScope = SyncRefreshScope(
            scheduling = true,
            workflow = true,
            care = true,
            device = true,
            communication = true,
        )

        fun fromDomains(domains: Set<ReplicaDomain>): SyncRefreshScope = SyncRefreshScope(
            scheduling = ReplicaDomain.SCHEDULING in domains,
            workflow = ReplicaDomain.WORKFLOW in domains,
            care = ReplicaDomain.CARE in domains,
            device = ReplicaDomain.DEVICE in domains,
            communication = ReplicaDomain.COMMUNICATION in domains,
        )
    }
}
