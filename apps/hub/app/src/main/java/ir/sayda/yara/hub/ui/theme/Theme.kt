package ir.sayda.yara.hub.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val YaraColorScheme = lightColorScheme(
    primary = SoftGreen,
    onPrimary = Color.White,
    secondary = SoftBlue,
    onSecondary = Color.White,
    tertiary = SoftOrange,
    onTertiary = Color.White,
    background = WarmWhite,
    onBackground = TextPrimary,
    surface = LightGray,
    onSurface = TextPrimary,
    error = SoftRed,
    onError = Color.White
)

@Composable
fun HubTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = YaraColorScheme,
        typography = Typography,
        content = content
    )
}
