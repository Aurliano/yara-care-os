package ir.sayda.yara.hub.feature.communication.components

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlin.math.min

data class CallLayoutTokens(
    val contentMaxWidth: Dp,
    val horizontalPadding: Dp,
    val verticalPadding: Dp,
    val avatarSize: Dp,
    val isLandscape: Boolean,
    val useSplitLayout: Boolean,
    val isTenInch: Boolean,
)

@Composable
fun rememberCallLayoutTokens(): CallLayoutTokens {
    val configuration = LocalConfiguration.current
    val fontScale = LocalDensity.current.fontScale
    return remember(configuration.screenWidthDp, configuration.screenHeightDp, fontScale) {
        val width = configuration.screenWidthDp
        val height = configuration.screenHeightDp
        val shortest = min(width, height)
        val isLandscape = width > height
        val isTenInch = shortest >= 720
        val isEightInch = shortest >= 600
        val largeFont = fontScale >= 1.3f
        CallLayoutTokens(
            contentMaxWidth = when {
                isTenInch && isLandscape -> 1100.dp
                isTenInch -> 840.dp
                isEightInch -> 720.dp
                else -> 640.dp
            },
            horizontalPadding = when {
                isTenInch -> 56.dp
                isEightInch -> 40.dp
                else -> 32.dp
            },
            verticalPadding = when {
                isLandscape -> 20.dp
                isTenInch -> 40.dp
                else -> 28.dp
            },
            avatarSize = when {
                largeFont -> 136.dp
                isTenInch && !isLandscape -> 196.dp
                isLandscape -> 128.dp
                isEightInch -> 168.dp
                else -> 148.dp
            },
            isLandscape = isLandscape,
            useSplitLayout = isLandscape && isEightInch && !largeFont,
            isTenInch = isTenInch,
        )
    }
}
