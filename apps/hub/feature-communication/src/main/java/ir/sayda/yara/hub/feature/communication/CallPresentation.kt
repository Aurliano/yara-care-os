package ir.sayda.yara.hub.feature.communication

import ir.sayda.yara.hub.core.communication.CallDirection
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.Contact

enum class CallScreenKind {
    Hidden,
    Incoming,
    Outgoing,
    Talking,
    ConnectionLost,
    Retry,
    Finished,
}

data class CallUiModel(
    val kind: CallScreenKind,
    val contactName: String,
    val headline: String,
    val status: String,
    val showAnswer: Boolean,
    val showDecline: Boolean,
    val showHangup: Boolean,
    val showRetry: Boolean,
    val showReturnHome: Boolean,
    val showMediaControls: Boolean,
    val showCamera: Boolean,
    val muted: Boolean,
    val cameraOn: Boolean,
)

object CallCopy {
    const val FAMILY = "خانواده"
    const val ANSWER = "پاسخ"
    const val DECLINE = "رد کردن"
    const val HANGUP = "قطع تماس"
    const val RETRY = "تلاش دوباره"
    const val RETURN_HOME = "بازگشت به خانه"
    const val MUTE = "بی‌صدا"
    const val UNMUTE = "صدا دار"
    const val SPEAKER = "بلندگو"
    const val CAMERA_ON = "دوربین روشن"
    const val CAMERA_OFF = "دوربین خاموش"
    const val START_FAILED = "الان نتوانستیم وصل شویم. دوباره تلاش کنید."
}

fun callScreenKind(
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

fun CallSession.resolvedContactName(contacts: List<Contact>, fallbackName: String = ""): String {
    fallbackName.trim().takeIf { it.isNotEmpty() }?.let { return it }
    contacts.firstOrNull { contact -> contact.id == recipientContactId }
        ?.displayName
        ?.trim()
        ?.takeIf { it.isNotEmpty() }
        ?.let { return it }
    return CallCopy.FAMILY
}

fun toCallUiModel(
    session: CallSession?,
    contactName: String,
    muted: Boolean = false,
    cameraOn: Boolean = false,
    startFailed: Boolean = false,
    awaitingOutgoing: Boolean = false,
    locallyFinished: Boolean = false,
): CallUiModel {
    val kind = callScreenKind(session, startFailed, awaitingOutgoing, locallyFinished)
    val name = contactName.trim().ifEmpty { CallCopy.FAMILY }
    val video = session?.channel.equals("VIDEO", ignoreCase = true)
    return when (kind) {
        CallScreenKind.Hidden -> CallUiModel(
            kind = kind,
            contactName = name,
            headline = "",
            status = "",
            showAnswer = false,
            showDecline = false,
            showHangup = false,
            showRetry = false,
            showReturnHome = false,
            showMediaControls = false,
            showCamera = false,
            muted = muted,
            cameraOn = cameraOn,
        )
        CallScreenKind.Incoming -> CallUiModel(
            kind = kind,
            contactName = name,
            headline = "تماس ورودی",
            status = "در حال وصل شدن...",
            showAnswer = true,
            showDecline = true,
            showHangup = false,
            showRetry = false,
            showReturnHome = false,
            showMediaControls = false,
            showCamera = false,
            muted = muted,
            cameraOn = cameraOn,
        )
        CallScreenKind.Outgoing -> CallUiModel(
            kind = kind,
            contactName = name,
            headline = "در حال تماس",
            status = "لطفاً کمی صبر کنید",
            showAnswer = false,
            showDecline = false,
            showHangup = true,
            showRetry = false,
            showReturnHome = false,
            showMediaControls = false,
            showCamera = false,
            muted = muted,
            cameraOn = cameraOn,
        )
        CallScreenKind.Talking -> CallUiModel(
            kind = kind,
            contactName = name,
            headline = "در حال گفتگو",
            status = if (muted) "صدا قطع است" else "تماس برقرار است",
            showAnswer = false,
            showDecline = false,
            showHangup = true,
            showRetry = false,
            showReturnHome = false,
            showMediaControls = true,
            showCamera = video,
            muted = muted,
            cameraOn = cameraOn,
        )
        CallScreenKind.ConnectionLost -> CallUiModel(
            kind = kind,
            contactName = name,
            headline = "ارتباط قطع شد",
            status = "نگران نباشید، می‌توانید دوباره وصل شوید",
            showAnswer = false,
            showDecline = false,
            showHangup = true,
            showRetry = true,
            showReturnHome = false,
            showMediaControls = false,
            showCamera = false,
            muted = muted,
            cameraOn = cameraOn,
        )
        CallScreenKind.Retry -> CallUiModel(
            kind = kind,
            contactName = name,
            headline = if (startFailed) "تماس برقرار نشد" else "در حال تلاش دوباره",
            status = if (startFailed) CallCopy.START_FAILED else "لطفاً کمی صبر کنید",
            showAnswer = false,
            showDecline = false,
            showHangup = !startFailed,
            showRetry = startFailed || session?.runtimeState == CallRuntimeState.ConnectionLost,
            showReturnHome = startFailed,
            showMediaControls = false,
            showCamera = false,
            muted = muted,
            cameraOn = cameraOn,
        )
        CallScreenKind.Finished -> CallUiModel(
            kind = kind,
            contactName = name,
            headline = "تماس پایان یافت",
            status = "می‌توانید به صفحه اصلی برگردید",
            showAnswer = false,
            showDecline = false,
            showHangup = false,
            showRetry = false,
            showReturnHome = true,
            showMediaControls = false,
            showCamera = false,
            muted = muted,
            cameraOn = cameraOn,
        )
    }
}
