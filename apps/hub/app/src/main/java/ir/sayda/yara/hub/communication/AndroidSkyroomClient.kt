package ir.sayda.yara.hub.communication

import android.annotation.SuppressLint
import android.content.Context
import android.media.AudioManager
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.communication.CallMediaEvent
import ir.sayda.yara.hub.core.communication.SkyroomClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

/**
 * Consumes a Backend-issued Skyroom login URL in a WebView.
 * Does not call Skyroom REST and does not store an API key.
 */
@Singleton
class AndroidSkyroomClient @Inject constructor(
    @ApplicationContext private val context: Context,
) : SkyroomClient {
    private val events = MutableSharedFlow<CallMediaEvent>(replay = 1, extraBufferCapacity = 16)
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private val _surface = MutableStateFlow<WebView?>(null)
    val surface: StateFlow<WebView?> = _surface.asStateFlow()
    private var webView: WebView? = null
    private var joined = false

    override fun observeEvents(): Flow<CallMediaEvent> = events.asSharedFlow()

    override suspend fun join(loginUrl: String) {
        withContext(Dispatchers.Main) {
            leaveInternal()
            val view = createWebView()
            webView = view
            _surface.value = view
            suspendCancellableCoroutine { continuation ->
                view.webViewClient = object : WebViewClient() {
                    override fun onPageFinished(view: WebView?, url: String?) {
                        if (continuation.isActive) {
                            joined = true
                            events.tryEmit(CallMediaEvent.Joined)
                            continuation.resume(Unit)
                        } else if (joined) {
                            events.tryEmit(CallMediaEvent.ConnectionRestored)
                        }
                    }

                    override fun onReceivedError(
                        view: WebView?,
                        request: WebResourceRequest?,
                        error: WebResourceError?,
                    ) {
                        events.tryEmit(CallMediaEvent.ConnectionLost)
                    }
                }
                view.loadUrl(loginUrl)
                continuation.invokeOnCancellation { leaveInternal() }
            }
        }
    }

    override suspend fun leave() {
        withContext(Dispatchers.Main) {
            leaveInternal()
            events.tryEmit(CallMediaEvent.Left)
        }
    }

    override suspend fun mute() {
        withContext(Dispatchers.Main) {
            audioManager.isMicrophoneMute = true
        }
    }

    override suspend fun unmute() {
        withContext(Dispatchers.Main) {
            audioManager.isMicrophoneMute = false
        }
    }

    override suspend fun cameraOn() {
        withContext(Dispatchers.Main) {
            webView?.evaluateJavascript(CAMERA_ON_SCRIPT, null)
        }
    }

    override suspend fun cameraOff() {
        withContext(Dispatchers.Main) {
            webView?.evaluateJavascript(CAMERA_OFF_SCRIPT, null)
        }
    }

    override suspend fun speaker() {
        withContext(Dispatchers.Main) {
            audioManager.mode = AudioManager.MODE_IN_COMMUNICATION
            audioManager.isSpeakerphoneOn = true
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun createWebView(): WebView {
        return WebView(context.applicationContext).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.mediaPlaybackRequiresUserGesture = false
            webChromeClient = object : WebChromeClient() {
                override fun onPermissionRequest(request: PermissionRequest?) {
                    request?.grant(request.resources)
                }
            }
        }
    }

    private fun leaveInternal() {
        joined = false
        _surface.value = null
        webView?.stopLoading()
        webView?.destroy()
        webView = null
        audioManager.isSpeakerphoneOn = false
        audioManager.isMicrophoneMute = false
        audioManager.mode = AudioManager.MODE_NORMAL
    }

    private companion object {
        const val CAMERA_ON_SCRIPT =
            "(function(){document.querySelectorAll('video').forEach(function(v){v.srcObject&&v.srcObject.getVideoTracks().forEach(function(t){t.enabled=true})})})()"
        const val CAMERA_OFF_SCRIPT =
            "(function(){document.querySelectorAll('video').forEach(function(v){v.srcObject&&v.srcObject.getVideoTracks().forEach(function(t){t.enabled=false})})})()"
    }
}
