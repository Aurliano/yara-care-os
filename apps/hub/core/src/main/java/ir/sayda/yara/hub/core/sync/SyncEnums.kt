package ir.sayda.yara.hub.core.sync

enum class SyncDirection {
    UPLOAD,
    DOWNLOAD,
}

enum class SyncSessionStatus {
    SYNCHRONIZATION_REQUESTED,
    SESSION_STARTED,
    SESSION_COMPLETED,
    SESSION_FAILED,
    SESSION_CANCELLED,
}

enum class OutboxEntryStatus {
    PENDING,
    IN_FLIGHT,
    COMPLETED,
    FAILED,
}

enum class PendingEvidenceStatus {
    PENDING,
    IN_FLIGHT,
    SUBMITTED,
    FAILED,
}

enum class OutboxOperationType {
    SUBMIT_DELTA,
    SUBMIT_SNAPSHOT,
    HUB_CONFIRMATION,
    HUB_DEVICE_STATE,
    HUB_COMMAND_DELIVER,
    HUB_COMMAND_COMPLETE,
    HUB_COMMAND_FAIL,
    HUB_SESSION_ACCEPT,
    HUB_SESSION_END,
    RUNTIME_PROCESS,
}
