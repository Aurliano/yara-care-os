package ir.sayda.yara.hub.data.device

import android.content.Context
import android.os.BatteryManager
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.network.api.HubIntegrationApi
import ir.sayda.yara.hub.network.dto.HubDeviceStateRequestDto
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HubDeviceStateReporter @Inject constructor(
    @ApplicationContext private val context: Context,
    private val authRepository: AuthRepository,
    private val hubIntegrationApi: HubIntegrationApi,
) {
    suspend fun reportOnline() {
        val deviceId = authRepository.getIdentity()?.deviceId ?: return
        val batteryPercent = readBatteryPercent()
        val currentState = buildJsonObject {
            put("network", JsonPrimitive("online"))
            if (batteryPercent != null) {
                put("battery_percent", JsonPrimitive(batteryPercent))
            }
        }
        runCatching {
            hubIntegrationApi.updateDeviceState(
                HubDeviceStateRequestDto(
                    deviceId = deviceId,
                    currentState = currentState,
                    isOnline = true,
                ),
            )
        }
    }

    private fun readBatteryPercent(): Int? {
        val manager = context.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager ?: return null
        val capacity = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        return capacity.takeIf { it in 0..100 }
    }
}
