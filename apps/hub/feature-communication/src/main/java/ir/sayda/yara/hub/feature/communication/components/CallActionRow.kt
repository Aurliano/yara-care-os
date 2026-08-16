package ir.sayda.yara.hub.feature.communication.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
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
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.feature.communication.R
import ir.sayda.yara.hub.feature.communication.presentation.CommunicationPresentationState
import ir.sayda.yara.hub.ui.components.CallActionButton
import ir.sayda.yara.hub.ui.components.CallIconButton
import ir.sayda.yara.hub.ui.theme.YaraTheme

@Composable
fun CallActionRow(
    state: CommunicationPresentationState,
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
    val tokens = YaraTheme.colors
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (state.showMediaControls) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.Top,
            ) {
                CallIconButton(
                    label = stringResource(if (state.muted) R.string.call_action_unmute else R.string.call_action_mute),
                    icon = if (state.muted) Icons.Rounded.MicOff else Icons.Rounded.Mic,
                    onClick = onToggleMute,
                    containerColor = if (state.muted) tokens.error.copy(alpha = 0.16f) else tokens.surface,
                    contentColor = if (state.muted) tokens.error else tokens.onSurface,
                )
                CallIconButton(
                    label = stringResource(R.string.call_action_speaker),
                    icon = Icons.Rounded.VolumeUp,
                    onClick = onSpeaker,
                    containerColor = tokens.wash,
                    contentColor = tokens.primary,
                )
                CallIconButton(
                    label = if (state.cameraEnabled) {
                        stringResource(
                            if (state.cameraOn) R.string.call_action_camera_off else R.string.call_action_camera_on,
                        )
                    } else {
                        stringResource(R.string.call_camera_unavailable)
                    },
                    icon = if (state.cameraOn) Icons.Rounded.Videocam else Icons.Rounded.VideocamOff,
                    onClick = onToggleCamera,
                    enabled = state.cameraEnabled,
                    containerColor = if (state.cameraOn && state.cameraEnabled) tokens.wash else tokens.surface,
                    contentColor = if (state.cameraOn && state.cameraEnabled) tokens.primary else tokens.onSurface,
                )
            }
            Spacer(modifier = Modifier.height(32.dp))
        }
        if (state.showAnswer) {
            CallActionButton(
                label = stringResource(R.string.call_action_answer),
                onClick = onAnswer,
                containerColor = tokens.primary,
                contentColor = tokens.onPrimary,
                icon = Icons.Rounded.Call,
            )
            Spacer(modifier = Modifier.height(16.dp))
        }
        if (state.showRetry) {
            CallActionButton(
                label = stringResource(R.string.call_action_retry),
                onClick = onRetry,
                containerColor = tokens.primary,
                contentColor = tokens.onPrimary,
                icon = Icons.Rounded.Refresh,
            )
            Spacer(modifier = Modifier.height(16.dp))
        }
        if (state.showDecline) {
            CallActionButton(
                label = stringResource(R.string.call_action_decline),
                onClick = onDecline,
                containerColor = tokens.error,
                contentColor = tokens.onError,
                icon = Icons.Rounded.CallEnd,
            )
            Spacer(modifier = Modifier.height(16.dp))
        }
        if (state.showHangup) {
            CallActionButton(
                label = stringResource(R.string.call_action_hangup),
                onClick = onHangup,
                containerColor = tokens.error,
                contentColor = tokens.onError,
                icon = Icons.Rounded.CallEnd,
            )
            Spacer(modifier = Modifier.height(16.dp))
        }
        if (state.showReturnHome) {
            CallActionButton(
                label = stringResource(R.string.call_action_return_home),
                onClick = onReturnHome,
                containerColor = tokens.primary,
                contentColor = tokens.onPrimary,
                icon = Icons.Rounded.Home,
            )
        }
    }
}
