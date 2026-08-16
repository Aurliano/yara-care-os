package ir.sayda.yara.hub.feature.communication

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.togetherWith
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.feature.communication.components.CallActionRow
import ir.sayda.yara.hub.feature.communication.components.CallHeader
import ir.sayda.yara.hub.feature.communication.components.CallLayoutTokens
import ir.sayda.yara.hub.feature.communication.components.CallStatusText
import ir.sayda.yara.hub.feature.communication.components.ConnectionBanner
import ir.sayda.yara.hub.feature.communication.components.ParticipantCard
import ir.sayda.yara.hub.feature.communication.components.rememberCallLayoutTokens
import ir.sayda.yara.hub.feature.communication.presentation.CallScreenKind
import ir.sayda.yara.hub.feature.communication.presentation.CommunicationPresentationState
import ir.sayda.yara.hub.feature.communication.talking.TalkingScreen
import ir.sayda.yara.hub.feature.communication.talking.VoiceFeaturePlaceholders
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.theme.YaraTheme
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
        state = ui,
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
    val layout = rememberCallLayoutTokens()
    CompositionLocalProvider(androidx.compose.ui.platform.LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            containerColor = YaraTheme.colors.background,
        ) { innerPadding ->
            Box(modifier = Modifier.fillMaxSize()) {
                TodayBackground(modifier = Modifier.fillMaxSize())
                AnimatedContent(
                    targetState = state,
                    contentKey = { it.kind },
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding),
                    transitionSpec = {
                        (fadeIn(animationSpec = tween(280)) + scaleIn(
                            initialScale = 0.98f,
                            animationSpec = tween(280),
                        )) togetherWith (fadeOut(animationSpec = tween(200)) + scaleOut(
                            targetScale = 1.02f,
                            animationSpec = tween(200),
                        ))
                    },
                    label = "call-presentation-state",
                ) { staged ->
                    if (staged.kind == CallScreenKind.Hidden) {
                        Box(modifier = Modifier.fillMaxSize())
                    } else {
                        CallStage(
                            state = staged,
                            layout = layout,
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
private fun CallStage(
    state: CommunicationPresentationState,
    layout: CallLayoutTokens,
    onAnswer: () -> Unit,
    onDecline: () -> Unit,
    onHangup: () -> Unit,
    onRetry: () -> Unit,
    onToggleMute: () -> Unit,
    onSpeaker: () -> Unit,
    onToggleCamera: () -> Unit,
    onReturnHome: () -> Unit,
) {
    val scroll = rememberScrollState()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scroll)
            .padding(horizontal = layout.horizontalPadding, vertical = layout.verticalPadding),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = layout.contentMaxWidth)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            if (state.kind == CallScreenKind.Talking) {
                if (layout.useSplitLayout) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(32.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(
                            modifier = Modifier.weight(1f),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            CallHeader(headlineRes = state.headlineRes)
                            Spacer(modifier = Modifier.height(8.dp))
                            ParticipantCard(name = state.contactName, avatarSize = layout.avatarSize)
                            Spacer(modifier = Modifier.height(12.dp))
                            CallStatusText(statusRes = state.statusRes)
                        }
                        Column(
                            modifier = Modifier.weight(1f),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            if (state.showVoicePlaceholders) {
                                VoiceFeaturePlaceholders()
                                Spacer(modifier = Modifier.height(24.dp))
                            }
                            CallActionRow(
                                state = state,
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
                } else {
                    TalkingScreen(
                        state = state,
                        layout = layout,
                        onHangup = onHangup,
                        onToggleMute = onToggleMute,
                        onSpeaker = onSpeaker,
                        onToggleCamera = onToggleCamera,
                    )
                }
            } else if (layout.useSplitLayout) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(32.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    CallIdentityColumn(
                        state = state,
                        layout = layout,
                        modifier = Modifier.weight(1f),
                    )
                    CallControlsColumn(
                        state = state,
                        onAnswer = onAnswer,
                        onDecline = onDecline,
                        onHangup = onHangup,
                        onRetry = onRetry,
                        onToggleMute = onToggleMute,
                        onSpeaker = onSpeaker,
                        onToggleCamera = onToggleCamera,
                        onReturnHome = onReturnHome,
                        modifier = Modifier.weight(1f),
                    )
                }
            } else {
                CallIdentityColumn(state = state, layout = layout)
                Spacer(modifier = Modifier.height(32.dp))
                CallControlsColumn(
                    state = state,
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

@Composable
private fun CallIdentityColumn(
    state: CommunicationPresentationState,
    layout: CallLayoutTokens,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CallHeader(headlineRes = state.headlineRes)
        Spacer(modifier = Modifier.height(8.dp))
        ParticipantCard(name = state.contactName, avatarSize = layout.avatarSize)
        if (state.bannerKind == null) {
            Spacer(modifier = Modifier.height(12.dp))
            CallStatusText(statusRes = state.statusRes)
        }
        state.bannerKind?.let { kind ->
            Spacer(modifier = Modifier.height(20.dp))
            ConnectionBanner(kind = kind)
        }
    }
}

@Composable
private fun CallControlsColumn(
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
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (state.showWaitingIndicator) {
            CallWaitingIndicator()
            Spacer(modifier = Modifier.height(28.dp))
        }
        CallActionRow(
            state = state,
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

@Composable
private fun CallWaitingIndicator(modifier: Modifier = Modifier) {
    val tokens = YaraTheme.colors
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        CircularProgressIndicator(
            color = tokens.primary,
            modifier = Modifier.size(56.dp),
            strokeWidth = 4.dp,
        )
        Text(
            text = stringResource(R.string.call_waiting),
            color = tokens.muted,
            style = MaterialTheme.typography.bodyLarge,
        )
    }
}
