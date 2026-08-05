package ir.sayda.yara.hub.database.dao

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CheckpointMonotonicTest {

    @Test
    fun checkpointNeverRollsBack() {
        var currentSequence = 10L
        fun advance(incoming: Long): Boolean {
            if (incoming <= currentSequence) return false
            currentSequence = incoming
            return true
        }

        assertFalse(advance(10))
        assertFalse(advance(9))
        assertTrue(advance(11))
        assertTrue(advance(15))
        assertFalse(advance(14))
        assertEquals(15L, currentSequence)
    }

    private fun assertEquals(expected: Long, actual: Long) {
        org.junit.Assert.assertEquals(expected, actual)
    }
}
