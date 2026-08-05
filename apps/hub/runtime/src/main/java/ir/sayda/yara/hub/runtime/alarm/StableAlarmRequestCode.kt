package ir.sayda.yara.hub.runtime.alarm

import java.util.UUID

fun stableAlarmRequestCode(occurrenceId: String): Int {
    return runCatching {
        val uuid = UUID.fromString(occurrenceId)
        (uuid.mostSignificantBits xor uuid.leastSignificantBits).toInt() and 0x7FFFFFFF
    }.getOrElse {
        occurrenceId.hashCode() and 0x7FFFFFFF
    }
}
