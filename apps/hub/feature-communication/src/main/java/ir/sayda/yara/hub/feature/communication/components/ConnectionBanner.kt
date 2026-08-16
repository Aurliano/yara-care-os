package ir.sayda.yara.hub.feature.communication.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import ir.sayda.yara.hub.feature.communication.R
import ir.sayda.yara.hub.feature.communication.presentation.ConnectionBannerKind
import ir.sayda.yara.hub.ui.theme.YaraTheme

@Composable
fun ConnectionBanner(
    kind: ConnectionBannerKind,
    modifier: Modifier = Modifier,
) {
    val tokens = YaraTheme.colors
    val (textRes, container, content) = when (kind) {
        ConnectionBannerKind.Lost -> Triple(
            R.string.call_lost_status,
            tokens.error.copy(alpha = 0.12f),
            tokens.error,
        )
        ConnectionBannerKind.Retrying -> Triple(
            R.string.call_retry_status,
            tokens.wash,
            tokens.primary,
        )
        ConnectionBannerKind.Failed -> Triple(
            R.string.call_failed_status,
            tokens.warning.copy(alpha = 0.16f),
            tokens.onBackground,
        )
    }
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        color = container,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 18.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center,
        ) {
            Text(
                text = stringResource(textRes),
                color = content,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center,
            )
        }
    }
}
