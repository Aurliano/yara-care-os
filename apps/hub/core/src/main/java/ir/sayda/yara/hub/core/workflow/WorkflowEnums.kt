package ir.sayda.yara.hub.core.workflow

enum class WorkflowExecutionStatus {
    PENDING,
    ACTIVE,
    CONFIRMED,
    MISSED,
    CANCELLED,
    FAILED,
}

enum class WorkflowActionType {
    SHOW_REMINDER,
    OPEN_COMPARTMENT,
    INITIATE_CALL,
    NOTIFY_CAREGIVER,
    PLAY_AUDIO,
    REQUEST_CONFIRMATION,
}
