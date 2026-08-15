package ir.sayda.yara.hub.network.logging

import android.util.Log

object HubNetworkLogger {
    private const val TAG = "YaraHub"

    fun provisioningRegisterAttempt(backendUrl: String, correlationId: String) {
        Log.i(TAG, "provisioning_register_attempt backend_url=$backendUrl correlation_id=$correlationId")
    }

    fun provisioningStarted(correlationId: String) {
        Log.i(TAG, "provisioning_started correlation_id=$correlationId")
    }

    fun provisioningCompleted(deviceId: String, correlationId: String) {
        Log.i(TAG, "provisioning_completed device_id=$deviceId correlation_id=$correlationId")
    }

    fun authenticationSuccess(deviceId: String, correlationId: String) {
        Log.i(TAG, "authentication_success device_id=$deviceId correlation_id=$correlationId")
    }

    fun authenticationRefresh(deviceId: String, correlationId: String) {
        Log.i(TAG, "authentication_refresh device_id=$deviceId correlation_id=$correlationId")
    }

    fun authenticationFailed(reason: String, correlationId: String) {
        Log.w(TAG, "authentication_failed reason=$reason correlation_id=$correlationId")
    }

    fun backendUnavailable(reason: String, correlationId: String) {
        Log.w(TAG, "backend_unavailable reason=$reason correlation_id=$correlationId")
    }
}
