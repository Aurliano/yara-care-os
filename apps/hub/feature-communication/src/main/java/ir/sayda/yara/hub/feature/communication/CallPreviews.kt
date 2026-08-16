package ir.sayda.yara.hub.feature.communication

import android.content.res.Configuration
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import ir.sayda.yara.hub.core.communication.CallDirection
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.feature.communication.presentation.CallScreenKind
import ir.sayda.yara.hub.feature.communication.presentation.CommunicationPresentationStateMapper
import ir.sayda.yara.hub.ui.theme.YaraTheme

@Preview(name = "Incoming", showBackground = true, widthDp = 800, heightDp = 1280)
@Composable
private fun IncomingCallPreview() {
    CallPreviewHost(kind = CallScreenKind.Incoming)
}

@Preview(name = "Outgoing", showBackground = true, widthDp = 800, heightDp = 1280)
@Composable
private fun OutgoingCallPreview() {
    CallPreviewHost(kind = CallScreenKind.Outgoing)
}

@Preview(name = "Connected", showBackground = true, widthDp = 800, heightDp = 1280)
@Composable
private fun ConnectedCallPreview() {
    CallPreviewHost(kind = CallScreenKind.Talking)
}

@Preview(name = "Retry", showBackground = true, widthDp = 800, heightDp = 1280)
@Composable
private fun RetryCallPreview() {
    CallPreviewHost(kind = CallScreenKind.Retry)
}

@Preview(name = "Finished", showBackground = true, widthDp = 800, heightDp = 1280)
@Composable
private fun FinishedCallPreview() {
    CallPreviewHost(kind = CallScreenKind.Finished)
}

@Preview(name = "Incoming 10 inch", showBackground = true, widthDp = 1200, heightDp = 1920)
@Composable
private fun IncomingTenInchPreview() {
    CallPreviewHost(kind = CallScreenKind.Incoming)
}

@Preview(name = "Connected Landscape", showBackground = true, widthDp = 1920, heightDp = 1200)
@Composable
private fun ConnectedLandscapePreview() {
    CallPreviewHost(kind = CallScreenKind.Talking)
}

@Preview(name = "Outgoing Landscape", showBackground = true, widthDp = 1920, heightDp = 1200)
@Composable
private fun OutgoingLandscapePreview() {
    CallPreviewHost(kind = CallScreenKind.Outgoing)
}

@Preview(name = "Connected Large Font", showBackground = true, widthDp = 800, heightDp = 1280, fontScale = 1.6f)
@Composable
private fun ConnectedLargeFontPreview() {
    CallPreviewHost(kind = CallScreenKind.Talking)
}

@Preview(
    name = "Incoming Dark Mode",
    showBackground = true,
    widthDp = 800,
    heightDp = 1280,
    uiMode = Configuration.UI_MODE_NIGHT_YES,
)
@Composable
private fun IncomingDarkPreview() {
    CallPreviewHost(kind = CallScreenKind.Incoming, darkTheme = true)
}

@Preview(
    name = "Finished Dark Mode",
    showBackground = true,
    widthDp = 1200,
    heightDp = 1920,
    uiMode = Configuration.UI_MODE_NIGHT_YES,
)
@Composable
private fun FinishedDarkTenInchPreview() {
    CallPreviewHost(kind = CallScreenKind.Finished, darkTheme = true)
}

@Composable
private fun CallPreviewHost(
    kind: CallScreenKind,
    darkTheme: Boolean = false,
) {
    YaraTheme(darkTheme = darkTheme) {
        CallScreen(
            state = previewState(kind),
            onAnswer = {},
            onDecline = {},
            onHangup = {},
            onRetry = {},
            onToggleMute = {},
            onSpeaker = {},
            onToggleCamera = {},
            onReturnHome = {},
        )
    }
}

private fun previewState(kind: CallScreenKind) = when (kind) {
    CallScreenKind.Incoming -> CommunicationPresentationStateMapper.map(
        session = previewSession(CallRuntimeState.Connecting, CallDirection.Incoming),
        contactName = "مادر",
    )
    CallScreenKind.Outgoing -> CommunicationPresentationStateMapper.map(
        session = previewSession(CallRuntimeState.Connecting, CallDirection.Outgoing),
        contactName = "پدر",
    )
    CallScreenKind.Talking -> CommunicationPresentationStateMapper.map(
        session = previewSession(CallRuntimeState.Connected, CallDirection.Outgoing, channel = "VOICE"),
        contactName = "خواهر",
    )
    CallScreenKind.Retry -> CommunicationPresentationStateMapper.map(
        session = previewSession(CallRuntimeState.Reconnecting, CallDirection.Outgoing),
        contactName = "عمو",
    )
    CallScreenKind.Finished -> CommunicationPresentationStateMapper.map(
        session = previewSession(CallRuntimeState.Finished, CallDirection.Outgoing),
        contactName = "مادر",
    )
    CallScreenKind.ConnectionLost -> CommunicationPresentationStateMapper.map(
        session = previewSession(CallRuntimeState.ConnectionLost, CallDirection.Outgoing),
        contactName = "خاله",
    )
    CallScreenKind.Hidden -> CommunicationPresentationStateMapper.map(
        session = null,
        contactName = "",
    )
}

private fun previewSession(
    state: CallRuntimeState,
    direction: CallDirection,
    channel: String = "VOICE",
) = CallSession(
    sessionId = "preview",
    elderId = "elder-1",
    channel = channel,
    recipientContactId = "c1",
    runtimeState = state,
    joinToken = "token",
    expiresAtEpochMillis = 1L,
    updatedAtEpochMillis = 1L,
    direction = direction,
)
