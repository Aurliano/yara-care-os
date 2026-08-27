package ir.sayda.yara.hub.communication

import android.content.Context
import android.media.AudioManager
import dagger.hilt.android.qualifiers.ApplicationContext
import io.livekit.android.LiveKit
import io.livekit.android.events.RoomEvent
import io.livekit.android.room.Room
import io.livekit.android.room.track.VideoTrack
import ir.sayda.yara.hub.BuildConfig
import ir.sayda.yara.hub.core.communication.CallMediaEvent
import ir.sayda.yara.hub.core.communication.LivekitClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Consumes a Backend-issued LiveKit JWT join token using native LiveKit WebRTC SDK.
 * Does not call vendor REST APIs and does not store root API keys/secrets.
 */
@Singleton
class AndroidLivekitClient @Inject constructor(
    @ApplicationContext private val context: Context,
) : LivekitClient {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val events = MutableSharedFlow<CallMediaEvent>(replay = 1, extraBufferCapacity = 16)
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager

    private val _remoteVideoTrack = MutableStateFlow<VideoTrack?>(null)
    val remoteVideoTrack: StateFlow<VideoTrack?> = _remoteVideoTrack.asStateFlow()

    private val _localVideoTrack = MutableStateFlow<VideoTrack?>(null)
    val localVideoTrack: StateFlow<VideoTrack?> = _localVideoTrack.asStateFlow()

    private var room: Room? = null
    private var eventsJob: Job? = null
    private var joined = false

    override fun observeEvents(): Flow<CallMediaEvent> = events.asSharedFlow()

    fun initVideoRenderer(renderer: io.livekit.android.renderer.SurfaceViewRenderer) {
        room?.initVideoRenderer(renderer)
    }

    override suspend fun join(loginUrl: String) {
        withContext(Dispatchers.Main) {
            leaveInternal()
            val (serverUrl, token) = parseJoinCredentials(loginUrl)
            val currentRoom = LiveKit.create(context.applicationContext)
            room = currentRoom

            eventsJob = scope.launch {
                currentRoom.events.events.collect { event ->
                    handleRoomEvent(event)
                }
            }

            audioManager.mode = AudioManager.MODE_IN_COMMUNICATION
            @Suppress("DEPRECATION")
            audioManager.isSpeakerphoneOn = true

            try {
                currentRoom.connect(serverUrl, token)
                joined = true
                try {
                    currentRoom.localParticipant.setMicrophoneEnabled(true)
                } catch (_: Exception) {
                }
                try {
                    currentRoom.localParticipant.setCameraEnabled(true)
                } catch (_: Exception) {
                }
                events.tryEmit(CallMediaEvent.Joined)
            } catch (e: Exception) {
                events.tryEmit(CallMediaEvent.ConnectionLost)
                leaveInternal()
                throw e
            }
        }
    }

    private fun handleRoomEvent(event: RoomEvent) {
        when (event) {
            is RoomEvent.Connected -> {
                joined = true
                events.tryEmit(CallMediaEvent.Joined)
            }
            is RoomEvent.Disconnected -> {
                if (joined) {
                    events.tryEmit(CallMediaEvent.ConnectionLost)
                }
            }
            is RoomEvent.Reconnecting -> {
                events.tryEmit(CallMediaEvent.ConnectionLost)
            }
            is RoomEvent.Reconnected -> {
                events.tryEmit(CallMediaEvent.ConnectionRestored)
            }
            is RoomEvent.TrackSubscribed -> {
                val track = event.track
                if (track is VideoTrack) {
                    _remoteVideoTrack.value = track
                }
            }
            is RoomEvent.TrackUnsubscribed -> {
                if (event.track == _remoteVideoTrack.value) {
                    _remoteVideoTrack.value = null
                }
            }
            else -> Unit
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
            room?.localParticipant?.setMicrophoneEnabled(false)
        }
    }

    override suspend fun unmute() {
        withContext(Dispatchers.Main) {
            audioManager.isMicrophoneMute = false
            room?.localParticipant?.setMicrophoneEnabled(true)
        }
    }

    override suspend fun cameraOn() {
        withContext(Dispatchers.Main) {
            room?.localParticipant?.setCameraEnabled(true)
        }
    }

    override suspend fun cameraOff() {
        withContext(Dispatchers.Main) {
            room?.localParticipant?.setCameraEnabled(false)
        }
    }

    override suspend fun speaker() {
        withContext(Dispatchers.Main) {
            audioManager.mode = AudioManager.MODE_IN_COMMUNICATION
            @Suppress("DEPRECATION")
            audioManager.isSpeakerphoneOn = true
        }
    }

    private fun leaveInternal() {
        joined = false
        eventsJob?.cancel()
        eventsJob = null
        _remoteVideoTrack.value = null
        _localVideoTrack.value = null
        room?.disconnect()
        room?.release()
        room = null
        @Suppress("DEPRECATION")
        audioManager.isSpeakerphoneOn = false
        audioManager.isMicrophoneMute = false
        audioManager.mode = AudioManager.MODE_NORMAL
    }

    private fun parseJoinCredentials(raw: String): Pair<String, String> {
        val trimmed = raw.trim()
        if (trimmed.startsWith("wss://") || trimmed.startsWith("ws://") || trimmed.startsWith("https://")) {
            val hashIndex = trimmed.indexOf('#')
            if (hashIndex != -1) {
                val url = trimmed.substring(0, hashIndex)
                val query = trimmed.substring(hashIndex + 1)
                val tokenParam = query.split("&").firstOrNull { it.startsWith("token=") }
                val token = tokenParam?.substringAfter("token=") ?: query
                return Pair(url, token)
            }
            val queryIndex = trimmed.indexOf('?')
            if (queryIndex != -1) {
                val url = trimmed.substring(0, queryIndex)
                val query = trimmed.substring(queryIndex + 1)
                val tokenParam = query.split("&").firstOrNull { it.startsWith("token=") }
                val token = tokenParam?.substringAfter("token=") ?: query
                return Pair(url, token)
            }
        }
        val defaultUrl = try {
            BuildConfig.LIVEKIT_URL
        } catch (_: Throwable) {
            "wss://livekit.yara.sayda.ir"
        }
        return Pair(defaultUrl, trimmed)
    }
}
