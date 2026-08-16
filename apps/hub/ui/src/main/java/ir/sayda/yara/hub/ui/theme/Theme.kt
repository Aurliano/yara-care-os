package ir.sayda.yara.hub.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

@Immutable
data class YaraColorTokens(
    val background: Color,
    val onBackground: Color,
    val surface: Color,
    val onSurface: Color,
    val primary: Color,
    val onPrimary: Color,
    val wash: Color,
    val secondary: Color,
    val onSecondary: Color,
    val tertiary: Color,
    val onTertiary: Color,
    val success: Color,
    val warning: Color,
    val error: Color,
    val onError: Color,
    val info: Color,
    val muted: Color,
    val mutedContainer: Color,
)

val LightYaraColors = YaraColorTokens(
    background = WarmWhite,
    onBackground = TextPrimary,
    surface = SurfaceGray,
    onSurface = TextPrimary,
    primary = YaraGreen,
    onPrimary = Color.White,
    wash = YaraLightGreen,
    secondary = SoftBlue,
    onSecondary = Color.White,
    tertiary = SoftOrange,
    onTertiary = Color.White,
    success = Success,
    warning = Warning,
    error = Error,
    onError = Color.White,
    info = Info,
    muted = TextSecondary,
    mutedContainer = SurfaceGray,
)

val DarkYaraColors = YaraColorTokens(
    background = Color(0xFF1C211E),
    onBackground = Color(0xFFF4F1EC),
    surface = Color(0xFF272E2A),
    onSurface = Color(0xFFF4F1EC),
    primary = Color(0xFF6FCB8E),
    onPrimary = Color(0xFF10301C),
    wash = Color(0xFF24352B),
    secondary = Color(0xFF8EC4F0),
    onSecondary = Color(0xFF102033),
    tertiary = Color(0xFFE0B07A),
    onTertiary = Color(0xFF2C1C0A),
    success = Color(0xFF6FCB8E),
    warning = Color(0xFFE0B07A),
    error = Color(0xFFE98989),
    onError = Color(0xFF2A1212),
    info = Color(0xFF8EC4F0),
    muted = Color(0xFFB3B8B4),
    mutedContainer = Color(0xFF323A36),
)

private val LightYaraColorScheme = lightColorScheme(
    primary = LightYaraColors.primary,
    onPrimary = LightYaraColors.onPrimary,
    secondary = LightYaraColors.secondary,
    onSecondary = LightYaraColors.onSecondary,
    tertiary = LightYaraColors.tertiary,
    onTertiary = LightYaraColors.onTertiary,
    background = LightYaraColors.background,
    onBackground = LightYaraColors.onBackground,
    surface = LightYaraColors.surface,
    onSurface = LightYaraColors.onSurface,
    error = LightYaraColors.error,
    onError = LightYaraColors.onError,
)

private val DarkYaraColorScheme = darkColorScheme(
    primary = DarkYaraColors.primary,
    onPrimary = DarkYaraColors.onPrimary,
    secondary = DarkYaraColors.secondary,
    onSecondary = DarkYaraColors.onSecondary,
    tertiary = DarkYaraColors.tertiary,
    onTertiary = DarkYaraColors.onTertiary,
    background = DarkYaraColors.background,
    onBackground = DarkYaraColors.onBackground,
    surface = DarkYaraColors.surface,
    onSurface = DarkYaraColors.onSurface,
    error = DarkYaraColors.error,
    onError = DarkYaraColors.onError,
)

internal val LocalYaraColors = staticCompositionLocalOf { LightYaraColors }

object YaraTheme {
    val colors: YaraColorTokens
        @Composable
        get() = LocalYaraColors.current
}

@Composable
fun YaraTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val tokens = if (darkTheme) DarkYaraColors else LightYaraColors
    val scheme = if (darkTheme) DarkYaraColorScheme else LightYaraColorScheme
    CompositionLocalProvider(LocalYaraColors provides tokens) {
        MaterialTheme(
            colorScheme = scheme,
            typography = Typography,
            content = content,
        )
    }
}

@Composable
fun HubTheme(content: @Composable () -> Unit) {
    YaraTheme(content = content)
}
