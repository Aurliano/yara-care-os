package ir.sayda.yara.hub.feature.communication.talking

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.CallEnd
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.MicOff
import androidx.compose.material.icons.rounded.Videocam
import androidx.compose.material.icons.rounded.VideocamOff
import androidx.compose.material.icons.rounded.VolumeUp
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.feature.communication.R
import ir.sayda.yara.hub.feature.communication.components.CallActionRow
import ir.sayda.yara.hub.feature.communication.components.CallHeader
import ir.sayda.yara.hub.feature.communication.components.CallLayoutTokens
import ir.sayda.yara.hub.feature.communication.components.CallStatusText
import ir.sayda.yara.hub.feature.communication.components.ParticipantCard
import ir.sayda.yara.hub.feature.communication.presentation.CommunicationPresentationState
import ir.sayda.yara.hub.ui.theme.YaraTheme

@Composable
fun TalkingScreen(
    state: CommunicationPresentationState,
    layout: CallLayoutTokens,
    onHangup: () -> Unit,
    onToggleMute: () -> Unit,
    onSpeaker: () -> Unit,
    onToggleCamera: () -> Unit,
    modifier: Modifier = Modifier,
) {
    if (state.cameraEnabled) {
        Box(
            modifier = modifier.fillMaxSize(),
            contentAlignment = Alignment.BottomCenter,
        ) {
            VideoCallBottomBar(
                state = state,
                onHangup = onHangup,
                onToggleMute = onToggleMute,
                onSpeaker = onSpeaker,
                onToggleCamera = onToggleCamera,
            )
        }
    } else {
        Column(
            modifier = modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            CallHeader(headlineRes = state.headlineRes)
            Spacer(modifier = Modifier.height(8.dp))
            ParticipantCard(name = state.contactName, avatarSize = layout.avatarSize)
            CallStatusText(statusRes = state.statusRes)
            Spacer(modifier = Modifier.weight(1f, fill = false))
            Spacer(modifier = Modifier.height(32.dp))
            Surface(
                shape = RoundedCornerShape(32.dp),
                color = YaraTheme.colors.surface,
                modifier = Modifier.padding(horizontal = 16.dp),
            ) {
                CallActionRow(
                    state = state,
                    onAnswer = {},
                    onDecline = {},
                    onHangup = onHangup,
                    onRetry = {},
                    onToggleMute = onToggleMute,
                    onSpeaker = onSpeaker,
                    onToggleCamera = onToggleCamera,
                    onReturnHome = {},
                    modifier = Modifier.padding(24.dp),
                )
            }
        }
    }
}

@Composable
private fun VideoCallBottomBar(
    state: CommunicationPresentationState,
    onHangup: () -> Unit,
    onToggleMute: () -> Unit,
    onSpeaker: () -> Unit,
    onToggleCamera: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val tokens = YaraTheme.colors
    Surface(
        shape = RoundedCornerShape(32.dp),
        color = tokens.surface.copy(alpha = 0.95f),
        shadowElevation = 8.dp,
        modifier = modifier
            .padding(horizontal = 16.dp, vertical = 28.dp)
            .widthIn(max = 480.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            VideoCallIconButton(
                label = stringResource(if (state.muted) R.string.call_action_unmute else R.string.call_action_mute),
                icon = if (state.muted) Icons.Rounded.MicOff else Icons.Rounded.Mic,
                onClick = onToggleMute,
                containerColor = if (state.muted) tokens.error.copy(alpha = 0.16f) else tokens.wash,
                contentColor = if (state.muted) tokens.error else tokens.onSurface,
            )
            VideoCallIconButton(
                label = stringResource(R.string.call_action_speaker),
                icon = Icons.Rounded.VolumeUp,
                onClick = onSpeaker,
                containerColor = tokens.wash,
                contentColor = tokens.primary,
            )
            VideoCallIconButton(
                label = stringResource(
                    if (state.cameraOn) R.string.call_action_camera_off else R.string.call_action_camera_on,
                ),
                icon = if (state.cameraOn) Icons.Rounded.Videocam else Icons.Rounded.VideocamOff,
                onClick = onToggleCamera,
                containerColor = if (state.cameraOn) tokens.wash else tokens.surface,
                contentColor = if (state.cameraOn) tokens.primary else tokens.onSurface,
            )
            VideoCallIconButton(
                label = stringResource(R.string.call_action_hangup),
                icon = Icons.Rounded.CallEnd,
                onClick = onHangup,
                containerColor = tokens.error,
                contentColor = tokens.onPrimary,
            )
        }
    }
}

@Composable
private fun VideoCallIconButton(
    label: String,
    icon: ImageVector,
    onClick: () -> Unit,
    containerColor: Color,
    contentColor: Color,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Surface(
            onClick = onClick,
            shape = CircleShape,
            color = containerColor,
            modifier = Modifier.size(64.dp),
        ) {
            Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                Icon(
                    imageVector = icon,
                    contentDescription = label,
                    tint = contentColor,
                    modifier = Modifier.size(32.dp),
                )
            }
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = YaraTheme.colors.onSurface,
            fontWeight = FontWeight.Medium,
        )
    }
}

