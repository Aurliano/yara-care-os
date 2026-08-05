package ir.sayda.yara.hub.core.scheduling

enum class OccurrenceStatus {
    SCHEDULED,
    DUE,
    CANCELLED,
    SKIPPED,
}

enum class ScheduleStatus {
    ACTIVE,
    PAUSED,
    ENDED,
    CANCELLED,
}
