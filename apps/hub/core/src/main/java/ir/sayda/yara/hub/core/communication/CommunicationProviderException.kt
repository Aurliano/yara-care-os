package ir.sayda.yara.hub.core.communication

/** Reason values mirror the Backend `reason` field; the vendor is never named. */
object ProviderFailureReason {
    const val NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    const val REJECTED = "PROVIDER_REJECTED"
    const val UNREACHABLE = "PROVIDER_UNREACHABLE"
    const val BUSY = "PROVIDER_BUSY"
    const val INVALID_RESPONSE = "PROVIDER_INVALID_RESPONSE"
}

class CommunicationProviderException(
    message: String,
    val reason: String = "",
) : IllegalStateException(message)
