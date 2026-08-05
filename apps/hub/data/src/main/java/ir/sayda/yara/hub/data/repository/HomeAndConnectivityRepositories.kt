package ir.sayda.yara.hub.data.repository

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.HomeRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConnectivityRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context,
) : ConnectivityRepository {

    override fun observeOnline(): Flow<Boolean> = flow {
        emit(isOnline())
    }.distinctUntilChanged()

    override suspend fun isOnline(): Boolean {
        val connectivityManager =
            context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }
}

@Singleton
class HomeRepositoryImpl @Inject constructor(
    private val authRepository: AuthRepository,
    private val workflowReplicaRepository: WorkflowReplicaRepository,
    private val communicationReplicaRepository: CommunicationReplicaRepository,
    private val replicaMetadataRepository: ReplicaMetadataRepository,
    private val connectivityRepository: ConnectivityRepository,
) : HomeRepository {

    override fun observeHomeSnapshot(): Flow<HomeRuntimeSnapshot> =
        combine(
            authRepository.observeIdentity(),
            workflowReplicaRepository.observeActiveExecutions(),
            replicaMetadataRepository.observeReplicaState(),
            connectivityRepository.observeOnline(),
        ) { identity, executions, replicaState, online ->
            HomeRuntimeSnapshot(
                elderDisplayName = identity?.elderId ?: "سالمند",
                activeExecutions = executions,
                priorityContacts = emptyList(),
                replicaHealth = replicaState?.health ?: "UNKNOWN",
                isOnline = online,
            )
        }
}
