package ir.sayda.yara.hub.feature.communication.components

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import ir.sayda.yara.hub.ui.theme.YaraTheme

@Composable
fun CallHeader(
    headlineRes: Int,
    modifier: Modifier = Modifier,
) {
    Text(
        text = stringResource(headlineRes),
        color = YaraTheme.colors.muted,
        style = MaterialTheme.typography.titleLarge,
        textAlign = TextAlign.Center,
        modifier = modifier,
    )
}
