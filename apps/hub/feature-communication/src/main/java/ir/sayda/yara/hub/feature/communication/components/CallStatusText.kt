package ir.sayda.yara.hub.feature.communication.components

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import ir.sayda.yara.hub.ui.theme.YaraTheme

@Composable
fun CallStatusText(
    statusRes: Int,
    modifier: Modifier = Modifier,
) {
    Text(
        text = stringResource(statusRes),
        color = YaraTheme.colors.muted,
        style = MaterialTheme.typography.bodyLarge,
        textAlign = TextAlign.Center,
        modifier = modifier,
    )
}
