package ir.sayda.yara.hub.core.provisioning

data class ProvisionCredential(
    val phone: String,
    val password: String,
)

interface HubDeviceCredentialsProvider {
    fun credentials(): ProvisionCredential?
}
