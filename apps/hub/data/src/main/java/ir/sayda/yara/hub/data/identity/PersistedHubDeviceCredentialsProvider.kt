package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.provisioning.HubLabCredentialDefaults
import ir.sayda.yara.hub.core.provisioning.ProvisionCredential
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PersistedHubDeviceCredentialsProvider @Inject constructor(
    private val identityStore: SecureHubIdentityStore,
    private val labDefaults: HubLabCredentialDefaults,
) : HubDeviceCredentialsProvider {
    override fun credentials(): ProvisionCredential? =
        identityStore.readCaregiverCredentials() ?: labDefaults.defaults()

    override fun suggestedCredentials(): ProvisionCredential? =
        identityStore.readCaregiverCredentials() ?: labDefaults.defaults()

    override fun saveCredentials(credential: ProvisionCredential) {
        identityStore.writeCaregiverCredentials(credential)
    }

    override fun clearCredentials() {
        identityStore.clearCaregiverCredentials()
    }
}
