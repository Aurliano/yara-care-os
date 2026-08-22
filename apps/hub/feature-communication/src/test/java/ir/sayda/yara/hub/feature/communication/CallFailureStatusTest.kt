package ir.sayda.yara.hub.feature.communication

import ir.sayda.yara.hub.core.communication.CommunicationProviderException
import ir.sayda.yara.hub.core.communication.ProviderFailureReason
import org.junit.Assert.assertEquals
import org.junit.Test

class CallFailureStatusTest {

    @Test
    fun reasonSelectsElderFriendlyStatus() {
        assertEquals(
            R.string.call_provider_not_configured,
            callFailureStatusRes(
                CommunicationProviderException("whatever", ProviderFailureReason.NOT_CONFIGURED),
            ),
        )
        assertEquals(
            R.string.call_provider_busy,
            callFailureStatusRes(CommunicationProviderException("busy", ProviderFailureReason.BUSY)),
        )
        assertEquals(
            R.string.call_provider_rejected,
            callFailureStatusRes(CommunicationProviderException("nope", ProviderFailureReason.REJECTED)),
        )
    }

    @Test
    fun unknownFailureFallsBackToGenericStatus() {
        assertEquals(R.string.call_failed_status, callFailureStatusRes(IllegalStateException("boom")))
    }

    @Test
    fun legacyDetailStillMapsWhenReasonIsMissing() {
        assertEquals(
            R.string.call_provider_unreachable,
            callFailureStatusRes(IllegalStateException("Communication provider is unreachable.")),
        )
    }
}
