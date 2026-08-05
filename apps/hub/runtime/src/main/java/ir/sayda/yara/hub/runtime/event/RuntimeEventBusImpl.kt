package ir.sayda.yara.hub.runtime.event

import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RuntimeEventBusImpl @Inject constructor() : RuntimeEventBus {

    private val events = MutableSharedFlow<RuntimeEvent>(extraBufferCapacity = 32)

    override suspend fun publish(event: RuntimeEvent) {
        events.emit(event)
    }

    override fun observe(): Flow<RuntimeEvent> = events.asSharedFlow()
}
