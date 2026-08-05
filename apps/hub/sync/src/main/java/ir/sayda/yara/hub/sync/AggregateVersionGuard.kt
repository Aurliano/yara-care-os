package ir.sayda.yara.hub.sync

enum class VersionComparison {
    INCOMING_OLDER,
    EQUAL,
    INCOMING_NEWER,
    NO_LOCAL,
}

object AggregateVersionGuard {
    fun compare(incoming: String, current: String?): VersionComparison {
        if (current == null) return VersionComparison.NO_LOCAL
        if (incoming == current) return VersionComparison.EQUAL
        return try {
            val incomingNum = incoming.toLong()
            val currentNum = current.toLong()
            when {
                incomingNum < currentNum -> VersionComparison.INCOMING_OLDER
                incomingNum > currentNum -> VersionComparison.INCOMING_NEWER
                else -> VersionComparison.EQUAL
            }
        } catch (_: NumberFormatException) {
            if (incoming < current) VersionComparison.INCOMING_OLDER else VersionComparison.INCOMING_NEWER
        }
    }
}
