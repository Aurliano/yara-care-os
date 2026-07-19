package ir.sayda.yara.hub.domain.model

/**
 * Domain model representing a medication task.
 */
data class Medication(
    val id: String,
    val name: String,
    val dosageTime: String,
    val isCompleted: Boolean = false
)
