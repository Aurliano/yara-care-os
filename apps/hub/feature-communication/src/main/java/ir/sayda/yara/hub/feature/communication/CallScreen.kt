package ir.sayda.yara.hub.feature.communication

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Call
import androidx.compose.material.icons.rounded.CallEnd
import androidx.compose.material.icons.rounded.Home
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.MicOff
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Videocam
import androidx.compose.material.icons.rounded.VideocamOff
import androidx.compose.material.icons.rounded.VolumeUp
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.ui.components.CallActionButton
import ir.sayda.yara.hub.ui.components.CallAvatar
import ir.sayda.yara.hub.ui.components.CallIconButton
import ir.sayda.yara.hub.ui.components.ReminderLoadingIndicator
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.theme.SoftRed
import ir.sayda.yara.hub.ui.theme.SurfaceGray
import ir.sayda.yara.hub.ui.theme.TextPrimary
import ir.sayda.yara.hub.ui.theme.TextSecondary
import ir.sayda.yara.hub.ui.theme.WarmWhite
import ir.sayda.yara.hub.ui.theme.YaraGreen
import ir.sayda.yara.hub.ui.theme.YaraLightGreen
import kotlinx.coroutines.delay

@Composable
fun CallRoute(
    args: CallViewArgs,
    onReturnHome: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: CallViewModel = hiltViewModel(),
) {
    val ui by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(args) {
        viewModel.prepare(args)
    }

    LaunchedEffect(ui.kind) {
        if (ui.kind == CallScreenKind.Finished) {
            delay(8_000)
            onReturnHome()
        }
    }

    CallScreen(
        ui = ui,
        onAnswer = viewModel::answer,
        onDecline = viewModel::hangup,
        onHangup = viewModel::hangup,
        onRetry = viewModel::retry,
        onToggleMute = viewModel::toggleMute,
        onSpeaker = viewModel::speaker,
        onToggleCamera = viewModel::toggleCamera,
        onReturnHome = onReturnHome,
        modifier = modifier,
    )
}

@Composable
fun CallScreen(
    ui: CallUiModel,
    onAnswer: () -> Unit,
    onDecline: () -> Unit,
    onHangup: () -> Unit,
    onRetry: () -> Unit,
    onToggleMute: () -> Unit,
    onSpeaker: () -> Unit,
    onToggleCamera: () -> Unit,
    onReturnHome: () -> Unit,
    modifier: Modifier = Modifier,
) {
    CompositionLocalProvider(androidx.compose.ui.platform.LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            containerColor = WarmWhite,
        ) { innerPadding ->
            Box(modifier = Modifier.fillMaxSize()) {
                TodayBackground(modifier = Modifier.fillMaxSize())
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .padding(horizontal = 40.dp, vertical = 32.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Column(
                        modifier = Modifier.widthIn(max = 720.dp).fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        CallAvatar(name = ui.contactName)
                        Spacer(modifier = Modifier.height(28.dp))
                        Text(
                            text = ui.headline,
                            color = TextSecondary,
                            style = MaterialTheme.typography.titleLarge,
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = ui.contactName,
                            color = TextPrimary,
                            style = MaterialTheme.typography.headlineLarge,
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = ui.status,
                            color = TextSecondary,
                            style = MaterialTheme.typography.bodyLarge,
                        )
                        if (ui.kind == CallScreenKind.Outgoing ||
                            (ui.kind == CallScreenKind.Retry && !ui.showRetry)
                        ) {
                            Spacer(modifier = Modifier.height(28.dp))
                            ReminderLoadingIndicator()
                        }
                        Spacer(modifier = Modifier.height(40.dp))
                        CallActions(
                            ui = ui,
                            onAnswer = onAnswer,
                            onDecline = onDecline,
                            onHangup = onHangup,
                            onRetry = onRetry,
                            onToggleMute = onToggleMute,
                            onSpeaker = onSpeaker,
                            onToggleCamera = onToggleCamera,
                            onReturnHome = onReturnHome,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CallActions(
    ui: CallUiModel,
    onAnswer: () -> Unit,
    onDecline: () -> Unit,
    onHangup: () -> Unit,
    onRetry: () -> Unit,
    onToggleMute: () -> Unit,
    onSpeaker: () -> Unit,
    onToggleCamera: () -> Unit,
    onReturnHome: () -> Unit,
) {
    if (ui.showMediaControls) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.Top,
        ) {
            CallIconButton(
                label = if (ui.muted) CallCopy.UNMUTE else CallCopy.MUTE,
                icon = if (ui.muted) Icons.Rounded.MicOff else Icons.Rounded.Mic,
                onClick = onToggleMute,
                containerColor = if (ui.muted) SoftRed.copy(alpha = 0.16f) else SurfaceGray,
                contentColor = if (ui.muted) SoftRed else TextPrimary,
            )
            CallIconButton(
                label = CallCopy.SPEAKER,
                icon = Icons.Rounded.VolumeUp,
                onClick = onSpeaker,
                containerColor = YaraLightGreen,
                contentColor = YaraGreen,
            )
            if (ui.showCamera) {
                CallIconButton(
                    label = if (ui.cameraOn) CallCopy.CAMERA_OFF else CallCopy.CAMERA_ON,
                    icon = if (ui.cameraOn) Icons.Rounded.Videocam else Icons.Rounded.VideocamOff,
                    onClick = onToggleCamera,
                    containerColor = if (ui.cameraOn) YaraLightGreen else SurfaceGray,
                    contentColor = if (ui.cameraOn) YaraGreen else TextPrimary,
                )
            }
        }
        Spacer(modifier = Modifier.height(32.dp))
    }
    if (ui.showAnswer) {
        CallActionButton(
            label = CallCopy.ANSWER,
            onClick = onAnswer,
            containerColor = YaraGreen,
            icon = Icons.Rounded.Call,
        )
        Spacer(modifier = Modifier.height(16.dp))
    }
    if (ui.showRetry) {
        CallActionButton(
            label = CallCopy.RETRY,
            onClick = onRetry,
            containerColor = YaraGreen,
            icon = Icons.Rounded.Refresh,
        )
        Spacer(modifier = Modifier.height(16.dp))
    }
    if (ui.showDecline) {
        CallActionButton(
            label = CallCopy.DECLINE,
            onClick = onDecline,
            containerColor = SoftRed,
            icon = Icons.Rounded.CallEnd,
        )
        Spacer(modifier = Modifier.height(16.dp))
    }
    if (ui.showHangup) {
        CallActionButton(
            label = CallCopy.HANGUP,
            onClick = onHangup,
            containerColor = SoftRed,
            icon = Icons.Rounded.CallEnd,
        )
        Spacer(modifier = Modifier.height(16.dp))
    }
    if (ui.showReturnHome) {
        CallActionButton(
            label = CallCopy.RETURN_HOME,
            onClick = onReturnHome,
            containerColor = YaraGreen,
            icon = Icons.Rounded.Home,
        )
    }
}
