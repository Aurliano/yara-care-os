package ir.sayda.yara.hub.runtime

import ir.sayda.yara.hub.core.runtime.RuntimeRefreshPort
import ir.sayda.yara.hub.core.sync.SyncRefreshScope
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.scheduling.SchedulingReplicaRuntime
import ir.sayda.yara.hub.runtime.workflow.WorkflowReplicaRuntime
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RuntimeRefreshCoordinator @Inject constructor(
    private val schedulingReplicaRuntime: SchedulingReplicaRuntime,
    private val workflowReplicaRuntime: WorkflowReplicaRuntime,
    private val runtimeAlarmCoordinator: RuntimeAlarmCoordinator,
) : RuntimeRefreshPort {

    override suspend fun refreshAfterSync(scope: SyncRefreshScope) {
        if (scope.isEmpty) return
        val now = System.currentTimeMillis()
        if (scope.scheduling || scope.care) {
            schedulingReplicaRuntime.hydrateAndEvaluate(now)
            runtimeAlarmCoordinator.syncAlarmsFromReplicas()
        }
        if (scope.workflow) {
            workflowReplicaRuntime.processDueOccurrences(now)
            workflowReplicaRuntime.dispatchActiveReminders()
        }
    }
}
