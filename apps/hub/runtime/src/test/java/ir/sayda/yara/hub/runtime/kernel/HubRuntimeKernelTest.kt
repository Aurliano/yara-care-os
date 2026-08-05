package ir.sayda.yara.hub.runtime.kernel

import ir.sayda.yara.hub.core.domain.model.RuntimeStateRecord
import ir.sayda.yara.hub.core.domain.repository.RuntimeStateRepository
import ir.sayda.yara.hub.core.runtime.IllegalRuntimeTransitionException
import ir.sayda.yara.hub.core.runtime.RuntimeComponent
import ir.sayda.yara.hub.core.runtime.RuntimeHealth
import ir.sayda.yara.hub.core.runtime.RuntimeKernelState
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HubRuntimeKernelTest {

    private val persisted = mutableListOf<RuntimeStateRecord>()

    private val repository = object : RuntimeStateRepository {
        override suspend fun upsert(record: RuntimeStateRecord) {
            persisted += record
        }

        override suspend fun get(componentId: String): RuntimeStateRecord? =
            persisted.lastOrNull { it.componentId == componentId }

        override suspend fun getAll(): List<RuntimeStateRecord> = persisted
    }

    private class TestComponent(
        override val componentId: String,
    ) : RuntimeComponent {
        override suspend fun initialize() = Unit
        override suspend fun recover() = Unit
        override suspend fun start() = Unit
        override suspend fun stop() = Unit
        override suspend fun health(): RuntimeHealth = RuntimeHealth(
            healthy = true,
            state = "RUNNING",
            detail = componentId,
        )
    }

    @Test
    fun initializeRecoverAndStartPersistKernelState() = runBlocking {
        val kernel = HubRuntimeKernel(repository)
        kernel.register(TestComponent("scheduling_replica_runtime"))

        kernel.initialize()
        assertEquals(RuntimeKernelState.INITIALIZING, kernel.kernelState)

        kernel.recover()
        assertEquals(RuntimeKernelState.RUNNING, kernel.kernelState)

        kernel.start()
        assertTrue(kernel.health().healthy)
        assertTrue(persisted.any { it.componentId == HubRuntimeKernel.KERNEL_COMPONENT_ID })
    }

    @Test(expected = IllegalRuntimeTransitionException::class)
    fun recoverRequiresInitializingState() = runBlocking {
        val kernel = HubRuntimeKernel(repository)
        kernel.register(TestComponent("test"))
        kernel.recover()
    }

    @Test
    fun stopTransitionsToStopped() = runBlocking {
        val kernel = HubRuntimeKernel(repository)
        kernel.register(TestComponent("test"))
        kernel.initialize()
        kernel.recover()
        kernel.stop()
        assertEquals(RuntimeKernelState.STOPPED, kernel.kernelState)
        assertFalse(kernel.health().healthy)
    }
}
