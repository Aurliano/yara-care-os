package ir.sayda.yara.hub.runtime

import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import ir.sayda.yara.hub.core.sync.SyncRefreshScope
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.scheduling.SchedulingCycleResult
import ir.sayda.yara.hub.runtime.scheduling.SchedulingReplicaRuntime
import ir.sayda.yara.hub.runtime.workflow.WorkflowReplicaRuntime
import kotlinx.coroutines.test.runTest
import org.junit.Test

class RuntimeRefreshCoordinatorTest {

    @Test
    fun conflictOnlyApplyPerformsNoRefresh() = runTest {
        val scheduling = mockk<SchedulingReplicaRuntime>(relaxed = true)
        val workflow = mockk<WorkflowReplicaRuntime>(relaxed = true)
        val alarms = mockk<RuntimeAlarmCoordinator>(relaxed = true)
        val coordinator = RuntimeRefreshCoordinator(scheduling, workflow, alarms)

        coordinator.refreshAfterSync(SyncRefreshScope())

        coVerify(exactly = 0) { scheduling.hydrateAndEvaluate(any()) }
        coVerify(exactly = 0) { workflow.processDueOccurrences(any()) }
    }

    @Test
    fun schedulingScopeRefreshesSchedulingOnly() = runTest {
        val scheduling = mockk<SchedulingReplicaRuntime>(relaxed = true)
        val workflow = mockk<WorkflowReplicaRuntime>(relaxed = true)
        val alarms = mockk<RuntimeAlarmCoordinator>(relaxed = true)
        coEvery { scheduling.hydrateAndEvaluate(any()) } returns SchedulingCycleResult(
            schedulesObserved = 0,
            occurrencesGenerated = 0,
            occurrencesMarkedDue = 0,
        )
        val coordinator = RuntimeRefreshCoordinator(scheduling, workflow, alarms)

        coordinator.refreshAfterSync(SyncRefreshScope(scheduling = true))

        coVerify(exactly = 1) { scheduling.hydrateAndEvaluate(any()) }
        coVerify(exactly = 0) { workflow.processDueOccurrences(any()) }
        coVerify(exactly = 1) { alarms.syncAlarmsFromReplicas(any()) }
    }
}
