package ir.sayda.yara.hub.data.provisioning

import org.junit.Assert.assertTrue
import org.junit.Test

class JwtExpiryParserTest {
    @Test
    fun parsesExpClaimFromJwtPayload() {
        val header = "eyJhbGciOiJIUzI1NiJ9"
        val payload = "eyJleHAiOjQwMDAwMDAwMDB9"
        val token = "$header.$payload.signature"
        val expiresAt = JwtExpiryParser.expiresAtEpochMillis(token, fallbackNow = 0L)
        assertTrue(expiresAt > 0L)
    }
}
