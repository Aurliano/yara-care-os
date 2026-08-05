package ir.sayda.yara.hub.runtime.support

import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmRegistry
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmSpec

class InMemoryOccurrenceAlarmRegistry : OccurrenceAlarmRegistry {
    val registered = linkedMapOf<String, OccurrenceAlarmSpec>()

    override suspend fun registerOccurrenceAlarm(spec: OccurrenceAlarmSpec) {
        if (isOccurrenceAlarmRegistered(spec.occurrenceId)) return
        registered[spec.occurrenceId] = spec
    }

    override suspend fun cancelOccurrenceAlarm(occurrenceId: String) {
        registered.remove(occurrenceId)
    }

    override suspend fun restoreAlarms(specs: List<OccurrenceAlarmSpec>) {
        val desiredIds = specs.map { it.occurrenceId }.toSet()
        registered.keys.filter { it !in desiredIds }.forEach { cancelOccurrenceAlarm(it) }
        specs.forEach { registerOccurrenceAlarm(it) }
    }

    override fun isOccurrenceAlarmRegistered(occurrenceId: String): Boolean =
        registered.containsKey(occurrenceId)

    override fun queryRegisteredOccurrenceIds(): Set<String> = registered.keys.toSet()
}
