package ir.sayda.yara.hub.communication

import android.view.ViewGroup
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.lifecycle.HiltViewModel
import io.livekit.android.renderer.SurfaceViewRenderer
import io.livekit.android.room.track.VideoTrack
import javax.inject.Inject

@HiltViewModel
class CallMediaViewModel @Inject constructor(
    private val livekitClient: AndroidLivekitClient,
) : ViewModel() {
    val remoteVideoTrack = livekitClient.remoteVideoTrack
    val localVideoTrack = livekitClient.localVideoTrack

    fun initVideoRenderer(renderer: SurfaceViewRenderer) {
        livekitClient.initVideoRenderer(renderer)
    }
}

/**
 * Pure LiveKit native WebRTC media surface for the Android Hub.
 * Renders full-screen video with hardware scaling and zero classroom chrome.
 */
@Composable
fun CallMediaSurface(
    modifier: Modifier = Modifier,
    viewModel: CallMediaViewModel = hiltViewModel(),
) {
    val remoteTrack by viewModel.remoteVideoTrack.collectAsStateWithLifecycle()
    if (remoteTrack != null) {
        LivekitVideoRenderer(
            videoTrack = remoteTrack,
            modifier = modifier.fillMaxSize(),
            onInitRenderer = { renderer -> viewModel.initVideoRenderer(renderer) },
        )
    }
}

@Composable
fun LivekitVideoRenderer(
    videoTrack: VideoTrack?,
    modifier: Modifier = Modifier,
    mirror: Boolean = false,
    onInitRenderer: (SurfaceViewRenderer) -> Unit = {},
) {
    val rendererRef = androidx.compose.runtime.remember {
        androidx.compose.runtime.mutableStateOf<SurfaceViewRenderer?>(null)
    }

    AndroidView(
        factory = { context ->
            SurfaceViewRenderer(context).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT,
                )
                setEnableHardwareScaler(true)
                onInitRenderer(this)
                rendererRef.value = this
            }
        },
        modifier = modifier,
        update = { renderer ->
            renderer.setMirror(mirror)
        },
        onRelease = { renderer ->
            rendererRef.value = null
            renderer.release()
        },
    )

    androidx.compose.runtime.DisposableEffect(videoTrack, rendererRef.value) {
        val currentTrack = videoTrack
        val currentRenderer = rendererRef.value
        if (currentTrack != null && currentRenderer != null) {
            currentTrack.addRenderer(currentRenderer)
        }
        onDispose {
            if (currentTrack != null && currentRenderer != null) {
                currentTrack.removeRenderer(currentRenderer)
            }
        }
    }
}
