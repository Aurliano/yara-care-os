package ir.sayda.yara.hub.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.BuildConfig
import ir.sayda.yara.hub.core.di.HubBaseUrl
import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.provisioning.ProvisionCredential
import ir.sayda.yara.hub.provisioning.HubDeviceModelCode
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object ProvisioningConfigModule {
    @Provides
    @HubBaseUrl
    fun provideHubBaseUrl(): String = BuildConfig.HUB_BACKEND_URL

    @Provides
    @Singleton
    fun provideHubDeviceModelCode(): HubDeviceModelCode = object : HubDeviceModelCode {
        override val value: String = BuildConfig.HUB_DEVICE_MODEL_CODE
    }

    @Provides
    @Singleton
    fun provideHubDeviceCredentialsProvider(): HubDeviceCredentialsProvider =
        object : HubDeviceCredentialsProvider {
        override fun credentials(): ProvisionCredential? {
            if (BuildConfig.PROVISION_PHONE.isBlank() || BuildConfig.PROVISION_PASSWORD.isBlank()) {
                return null
            }
            return ProvisionCredential(
                phone = BuildConfig.PROVISION_PHONE,
                password = BuildConfig.PROVISION_PASSWORD,
            )
        }
    }
}
