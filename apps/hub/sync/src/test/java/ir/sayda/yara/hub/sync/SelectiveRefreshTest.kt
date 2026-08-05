package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.sync.ReplicaDomain
import ir.sayda.yara.hub.core.sync.SyncRefreshScope
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SelectiveRefreshTest {

    @Test
    fun schedulingOnlyScopeDoesNotIncludeWorkflow() {
        val scope = SyncRefreshScope.fromDomains(setOf(ReplicaDomain.SCHEDULING))
        assertTrue(scope.scheduling)
        assertFalse(scope.workflow)
    }

    @Test
    fun emptyDomainsYieldEmptyScope() {
        assertTrue(SyncRefreshScope.fromDomains(emptySet()).isEmpty)
    }
}
