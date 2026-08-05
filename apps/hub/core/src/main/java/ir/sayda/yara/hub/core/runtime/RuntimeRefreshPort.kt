package ir.sayda.yara.hub.core.runtime

import ir.sayda.yara.hub.core.sync.SyncRefreshScope

interface RuntimeRefreshPort {
    suspend fun refreshAfterSync(scope: SyncRefreshScope)
}
