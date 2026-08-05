package ir.sayda.yara.hub.sync

import org.junit.Assert.assertEquals
import org.junit.Test

class AggregateVersionGuardTest {

    @Test
    fun acceptsNewerNumericVersion() {
        assertEquals(
            VersionComparison.INCOMING_NEWER,
            AggregateVersionGuard.compare("5", "4"),
        )
    }

    @Test
    fun skipsEqualVersion() {
        assertEquals(
            VersionComparison.EQUAL,
            AggregateVersionGuard.compare("7", "7"),
        )
    }

    @Test
    fun recordsConflictForStaleVersion() {
        assertEquals(
            VersionComparison.INCOMING_OLDER,
            AggregateVersionGuard.compare("3", "9"),
        )
    }

    @Test
    fun appliesWhenNoLocalVersion() {
        assertEquals(
            VersionComparison.NO_LOCAL,
            AggregateVersionGuard.compare("1", null),
        )
    }
}
