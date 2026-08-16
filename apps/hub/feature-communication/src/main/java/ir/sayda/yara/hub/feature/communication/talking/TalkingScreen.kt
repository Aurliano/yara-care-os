package ir.sayda.yara.hub.feature.communication.talking

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
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
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CallHeader(headlineRes = state.headlineRes)
        Spacer(modifier = Modifier.height(8.dp))
        ParticipantCard(name = state.contactName, avatarSize = layout.avatarSize)
        CallStatusText(statusRes = state.statusRes)
        if (state.showVoicePlaceholders) {
            Spacer(modifier = Modifier.height(24.dp))
            VoiceFeaturePlaceholders()
        }
        Spacer(modifier = Modifier.height(32.dp))
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
        )
    }
}

@Composable
fun VoiceFeaturePlaceholders(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        VoicePlaceholderSlot(label = stringResource(R.string.call_voice_waveform_placeholder))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            VoicePlaceholderSlot(
                label = stringResource(R.string.call_voice_recording_placeholder),
                modifier = Modifier.weight(1f),
            )
            VoicePlaceholderSlot(
                label = stringResource(R.string.call_voice_playback_placeholder),
                modifier = Modifier.weight(1f),
            )
        }
        VoicePlaceholderSlot(label = stringResource(R.string.call_voice_duration_placeholder))
    }
}

@Composable
private fun VoicePlaceholderSlot(
    label: String,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = YaraTheme.colors.surface,
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
                .padding(horizontal = 16.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = label,
                color = YaraTheme.colors.muted,
                style = MaterialTheme.typography.labelMedium,
            )
        }
    }
}
