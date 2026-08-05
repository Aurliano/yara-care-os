package ir.sayda.yara.hub.data.identity

import java.util.concurrent.atomic.AtomicReference
import javax.inject.Inject
import javax.inject.Singleton

data class IdentitySnapshot(
    val deviceId: String? = null,
    val replicaId: String? = null,
    val accessToken: String? = null,
    val refreshToken: String? = null,
    val tokenExpiresAtEpochMillis: Long = 0L,
)

@Singleton
class IdentitySnapshotHolder @Inject constructor() {
    private val snapshot = AtomicReference(IdentitySnapshot())

    fun get(): IdentitySnapshot = snapshot.get()

    fun update(transform: (IdentitySnapshot) -> IdentitySnapshot) {
        snapshot.updateAndGet(transform)
    }

    fun set(value: IdentitySnapshot) {
        snapshot.set(value)
    }

    fun clear() {
        snapshot.set(IdentitySnapshot())
    }
}
