package ir.sayda.yara.hub.feature.communication.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.feature.communication.R
import ir.sayda.yara.hub.ui.components.CallAvatar
import ir.sayda.yara.hub.ui.theme.YaraTheme

@Composable
fun ParticipantCard(
    name: String,
    avatarSize: Dp,
    modifier: Modifier = Modifier,
) {
    val displayName = name.ifBlank { stringResource(R.string.call_family_fallback) }
    val photoDescription = stringResource(R.string.call_participant_photo)
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CallAvatar(
            name = displayName,
            size = avatarSize,
            modifier = Modifier.semantics { contentDescription = photoDescription },
        )
        Spacer(modifier = Modifier.height(20.dp))
        Text(
            text = displayName,
            color = YaraTheme.colors.onBackground,
            style = MaterialTheme.typography.headlineLarge,
            textAlign = TextAlign.Center,
        )
    }
}
