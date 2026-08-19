package ir.sayda.yara.hub.feature.communication.presentation

import ir.sayda.yara.hub.core.communication.CallDirection
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.feature.communication.R

enum class CallScreenKind {
    Hidden,
    Incoming,
    Outgoing,
    Talking,
    ConnectionLost,
    Retry,
    Finished,
}

enum class ConnectionBannerKind {
    Lost,
    Retrying,
    Failed,
}

data class CommunicationPresentationState(
    val kind: CallScreenKind,
    val contactName: String,
    val headlineRes: Int,
    val statusRes: Int,
    val showAnswer: Boolean,
    val showDecline: Boolean,
    val showHangup: Boolean,
    val showRetry: Boolean,
    val showReturnHome: Boolean,
    val showMediaControls: Boolean,
    val cameraEnabled: Boolean,
    val muted: Boolean,
    val cameraOn: Boolean,
    val showWaitingIndicator: Boolean,
    val bannerKind: ConnectionBannerKind?,
    val showVoicePlaceholders: Boolean,
)

object CommunicationPresentationStateMapper {

    fun map(
        session: CallSession?,
        contactName: String,
        muted: Boolean = false,
        cameraOn: Boolean = false,
        startFailed: Boolean = false,
        startFailedStatusRes: Int? = null,
        awaitingOutgoing: Boolean = false,
        locallyFinished: Boolean = false,
    ): CommunicationPresentationState {
        val kind = kindFor(session, startFailed, awaitingOutgoing, locallyFinished)
        val name = contactName.trim()
        val video = session?.channel.equals("VIDEO", ignoreCase = true)
        return when (kind) {
            CallScreenKind.Hidden -> CommunicationPresentationState(
                kind = kind,
                contactName = name,
                headlineRes = R.string.call_outgoing_headline,
                statusRes = R.string.call_outgoing_status,
                showAnswer = false,
                showDecline = false,
                showHangup = false,
                showRetry = false,
                showReturnHome = false,
                showMediaControls = false,
                cameraEnabled = false,
                muted = muted,
                cameraOn = cameraOn,
                showWaitingIndicator = false,
                bannerKind = null,
                showVoicePlaceholders = false,
            )
            CallScreenKind.Incoming -> CommunicationPresentationState(
                kind = kind,
                contactName = name,
                headlineRes = R.string.call_incoming_headline,
                statusRes = R.string.call_incoming_status,
                showAnswer = true,
                showDecline = true,
                showHangup = false,
                showRetry = false,
                showReturnHome = false,
                showMediaControls = false,
                cameraEnabled = false,
                muted = muted,
                cameraOn = cameraOn,
                showWaitingIndicator = false,
                bannerKind = null,
                showVoicePlaceholders = false,
            )
            CallScreenKind.Outgoing -> CommunicationPresentationState(
                kind = kind,
                contactName = name,
                headlineRes = R.string.call_outgoing_headline,
                statusRes = R.string.call_outgoing_status,
                showAnswer = false,
                showDecline = false,
                showHangup = true,
                showRetry = false,
                showReturnHome = false,
                showMediaControls = false,
                cameraEnabled = false,
                muted = muted,
                cameraOn = cameraOn,
                showWaitingIndicator = true,
                bannerKind = null,
                showVoicePlaceholders = false,
            )
            CallScreenKind.Talking -> CommunicationPresentationState(
                kind = kind,
                contactName = name,
                headlineRes = R.string.call_talking_headline,
                statusRes = if (muted) R.string.call_talking_muted_status else R.string.call_talking_status,
                showAnswer = false,
                showDecline = false,
                showHangup = true,
                showRetry = false,
                showReturnHome = false,
                showMediaControls = true,
                cameraEnabled = video,
                muted = muted,
                cameraOn = cameraOn && video,
                showWaitingIndicator = false,
                bannerKind = null,
                showVoicePlaceholders = !video,
            )
            CallScreenKind.ConnectionLost -> CommunicationPresentationState(
                kind = kind,
                contactName = name,
                headlineRes = R.string.call_lost_headline,
                statusRes = R.string.call_lost_status,
                showAnswer = false,
                showDecline = false,
                showHangup = true,
                showRetry = true,
                showReturnHome = false,
                showMediaControls = false,
                cameraEnabled = false,
                muted = muted,
                cameraOn = cameraOn,
                showWaitingIndicator = false,
                bannerKind = ConnectionBannerKind.Lost,
                showVoicePlaceholders = false,
            )
            CallScreenKind.Retry -> if (startFailed) {
                CommunicationPresentationState(
                    kind = kind,
                    contactName = name,
                    headlineRes = R.string.call_failed_headline,
                    statusRes = startFailedStatusRes ?: R.string.call_failed_status,
                    showAnswer = false,
                    showDecline = false,
                    showHangup = false,
                    showRetry = true,
                    showReturnHome = true,
                    showMediaControls = false,
                    cameraEnabled = false,
                    muted = muted,
                    cameraOn = cameraOn,
                    showWaitingIndicator = false,
                    bannerKind = ConnectionBannerKind.Failed,
                    showVoicePlaceholders = false,
                )
            } else {
                CommunicationPresentationState(
                    kind = kind,
                    contactName = name,
                    headlineRes = R.string.call_retry_headline,
                    statusRes = R.string.call_retry_status,
                    showAnswer = false,
                    showDecline = false,
                    showHangup = true,
                    showRetry = false,
                    showReturnHome = false,
                    showMediaControls = false,
                    cameraEnabled = false,
                    muted = muted,
                    cameraOn = cameraOn,
                    showWaitingIndicator = true,
                    bannerKind = ConnectionBannerKind.Retrying,
                    showVoicePlaceholders = false,
                )
            }
            CallScreenKind.Finished -> CommunicationPresentationState(
                kind = kind,
                contactName = name,
                headlineRes = R.string.call_finished_headline,
                statusRes = R.string.call_finished_status,
                showAnswer = false,
                showDecline = false,
                showHangup = false,
                showRetry = false,
                showReturnHome = true,
                showMediaControls = false,
                cameraEnabled = false,
                muted = muted,
                cameraOn = cameraOn,
                showWaitingIndicator = false,
                bannerKind = null,
                showVoicePlaceholders = false,
            )
        }
    }

    fun kindFor(
        session: CallSession?,
        startFailed: Boolean = false,
        awaitingOutgoing: Boolean = false,
        locallyFinished: Boolean = false,
    ): CallScreenKind {
        if (locallyFinished) return CallScreenKind.Finished
        if (startFailed && (session == null || session.runtimeState == CallRuntimeState.Idle)) {
            return CallScreenKind.Retry
        }
        if (awaitingOutgoing && (session == null || session.runtimeState == CallRuntimeState.Idle)) {
            return CallScreenKind.Outgoing
        }
        val current = session ?: return CallScreenKind.Hidden
        return when (current.runtimeState) {
            CallRuntimeState.Idle -> CallScreenKind.Hidden
            CallRuntimeState.Connecting -> if (current.direction == CallDirection.Incoming) {
                CallScreenKind.Incoming
            } else {
                CallScreenKind.Outgoing
            }
            CallRuntimeState.Connected -> CallScreenKind.Talking
            CallRuntimeState.ConnectionLost -> CallScreenKind.ConnectionLost
            CallRuntimeState.Reconnecting -> CallScreenKind.Retry
            CallRuntimeState.Finished -> CallScreenKind.Finished
        }
    }

    fun resolvedContactName(
        session: CallSession,
        contacts: List<Contact>,
        fallbackName: String = "",
    ): String {
        fallbackName.trim().takeIf { it.isNotEmpty() }?.let { return it }
        return contacts.firstOrNull { contact -> contact.id == session.recipientContactId }
            ?.displayName
            ?.trim()
            ?.takeIf { it.isNotEmpty() }
            .orEmpty()
    }
}
