package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.sync.SyncOperation
import ir.sayda.yara.hub.core.sync.SyncOperationType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SnapshotOperationClassificationTest {
    @Test
    fun snapshotTypeAndPayloadSuffixAreSnapshots() {
        assertTrue(isSnapshotOperation(operation(SyncOperationType.SNAPSHOT, "hub.replica.snapshot")))
        assertTrue(isSnapshotOperation(operation(SyncOperationType.DELTA, "care.activity.snapshot")))
        assertFalse(isSnapshotOperation(operation(SyncOperationType.DELTA, "care.activity.delta")))
    }

    @Test
    fun pendingListKeepsSnapshotsAfterFirstCheckpoint() {
        val pending = listOf(
            operation(SyncOperationType.SNAPSHOT, "hub.replica.snapshot", id = "snap"),
            operation(SyncOperationType.DELTA, "care.activity.delta", id = "delta"),
        )
        val snapshots = pending.filter(::isSnapshotOperation)
        val deltas = pending.filterNot(::isSnapshotOperation)
        assertEquals(listOf("snap"), snapshots.map { it.id })
        assertEquals(listOf("delta"), deltas.map { it.id })
    }

    private fun operation(
        type: SyncOperationType,
        payloadType: String,
        id: String = "op",
    ) = SyncOperation(
        id = id,
        operationType = type,
        aggregateReference = "agg",
        aggregateVersion = "1",
        payloadType = payloadType,
        payloadHash = "hash",
        payloadJson = "{}",
        status = "PENDING",
    )
}
