package ir.sayda.yara.hub.communication

import android.view.ViewGroup
import android.webkit.WebView
import android.widget.FrameLayout
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class CallMediaViewModel @Inject constructor(
    client: AndroidSkyroomClient,
) : ViewModel() {
    val surface = client.surface
}

@Composable
fun CallMediaSurface(
    modifier: Modifier = Modifier,
    viewModel: CallMediaViewModel = hiltViewModel(),
) {
    val webView by viewModel.surface.collectAsStateWithLifecycle()
    val current = webView ?: return
    AndroidView(
        factory = { context ->
            FrameLayout(context).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT,
                )
            }
        },
        modifier = modifier
            .fillMaxWidth()
            .fillMaxHeight(0.55f),
        update = { frame ->
            (current.parent as? ViewGroup)?.removeView(current)
            frame.removeAllViews()
            current.layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT,
            )
            frame.addView(current)
        },
    )
}
