package ir.sayda.yara.hub.core.result

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class AppResultTest {
    @Test
    fun successGetOrNullReturnsValue() {
        val result = AppResult.Success(42)
        assertEquals(42, result.getOrNull())
    }

    @Test
    fun errorGetOrNullReturnsNull() {
        val result = AppResult.Error(IllegalStateException("failed"))
        assertNull(result.getOrNull())
    }
}
