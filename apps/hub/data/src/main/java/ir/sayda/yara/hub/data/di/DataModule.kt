package ir.sayda.yara.hub.data.di

import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.core.di.DefaultDispatcher
import ir.sayda.yara.hub.core.di.IoDispatcher
import ir.sayda.yara.hub.core.communication.CommunicationGateway
import ir.sayda.yara.hub.core.communication.CommunicationRepository
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.DeviceReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.HomeRepository
import ir.sayda.yara.hub.core.domain.repository.IntegrationRuntimeRepository
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.repository.RuntimeStateRepository
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaSnapshotWriter
import ir.sayda.yara.hub.core.sync.SyncApplyTransaction
import ir.sayda.yara.hub.core.domain.repository.SyncConflictRepository
import ir.sayda.yara.hub.core.domain.repository.SyncSessionLocalRepository
import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.domain.usecase.ObserveHomeSnapshotUseCase
import ir.sayda.yara.hub.core.domain.usecase.ObserveHubIdentityUseCase
import ir.sayda.yara.hub.core.domain.repository.ReminderRepository
import ir.sayda.yara.hub.core.domain.usecase.ObserveReminderPresentationUseCase
import ir.sayda.yara.hub.core.domain.usecase.ObserveReplicaStateUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.domain.usecase.StartSynchronizationUseCase
import ir.sayda.yara.hub.data.repository.ReminderRepositoryImpl
import ir.sayda.yara.hub.data.identity.AuthRepositoryImpl
import ir.sayda.yara.hub.data.identity.AuthTokenRefreshHandler
import ir.sayda.yara.hub.data.identity.DataStoreReplicaIdentityProvider
import ir.sayda.yara.hub.data.identity.PersistedHubDeviceCredentialsProvider
import ir.sayda.yara.hub.data.provisioning.ProvisioningRepositoryImpl
import ir.sayda.yara.hub.data.provisioning.RuntimeProvisioningGateImpl
import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import ir.sayda.yara.hub.data.communication.CommunicationGatewayImpl
import ir.sayda.yara.hub.data.communication.CommunicationRepositoryImpl
import ir.sayda.yara.hub.data.repository.CareReplicaRepositoryImpl
import ir.sayda.yara.hub.data.repository.CommunicationReplicaRepositoryImpl
import ir.sayda.yara.hub.data.repository.ConnectivityRepositoryImpl
import ir.sayda.yara.hub.data.repository.DeviceReplicaRepositoryImpl
import ir.sayda.yara.hub.data.repository.HomeRepositoryImpl
import ir.sayda.yara.hub.data.repository.IntegrationRuntimeRepositoryImpl
import ir.sayda.yara.hub.data.repository.OutboxRepositoryImpl
import ir.sayda.yara.hub.data.repository.PendingEvidenceRepositoryImpl
import ir.sayda.yara.hub.data.repository.ReplicaMetadataRepositoryImpl
import ir.sayda.yara.hub.data.repository.RuntimeStateRepositoryImpl
import ir.sayda.yara.hub.data.repository.ReplicaSnapshotWriterImpl
import ir.sayda.yara.hub.data.repository.SchedulingReplicaRepositoryImpl
import ir.sayda.yara.hub.data.repository.SyncConflictRepositoryImpl
import ir.sayda.yara.hub.data.repository.SyncSessionLocalRepositoryImpl
import ir.sayda.yara.hub.data.repository.SyncApplyTransactionImpl
import ir.sayda.yara.hub.data.repository.SynchronizationRepositoryImpl
import ir.sayda.yara.hub.data.repository.WorkflowReplicaRepositoryImpl
import ir.sayda.yara.hub.data.usecase.ObserveHomeSnapshotUseCaseImpl
import ir.sayda.yara.hub.data.usecase.ObserveHubIdentityUseCaseImpl
import ir.sayda.yara.hub.data.usecase.ObserveReplicaStateUseCaseImpl
import ir.sayda.yara.hub.data.usecase.ObserveReminderPresentationUseCaseImpl
import ir.sayda.yara.hub.data.usecase.StartSynchronizationUseCaseImpl
import ir.sayda.yara.hub.network.auth.TokenRefreshHandler
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.identity.ReplicaIdentityProvider
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds @Singleton abstract fun bindAuthRepository(impl: AuthRepositoryImpl): AuthRepository
    @Binds @Singleton abstract fun bindHubDeviceCredentialsProvider(
        impl: PersistedHubDeviceCredentialsProvider,
    ): ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
    @Binds @Singleton abstract fun bindTokenRefreshHandler(impl: AuthTokenRefreshHandler): TokenRefreshHandler
    @Binds @Singleton abstract fun bindProvisioningRepository(impl: ProvisioningRepositoryImpl): ProvisioningRepository
    @Binds @Singleton abstract fun bindRuntimeProvisioningGate(impl: RuntimeProvisioningGateImpl): RuntimeProvisioningGate
    @Binds @Singleton abstract fun bindCareReplicaRepository(impl: CareReplicaRepositoryImpl): CareReplicaRepository
    @Binds @Singleton abstract fun bindSchedulingReplicaRepository(impl: SchedulingReplicaRepositoryImpl): SchedulingReplicaRepository
    @Binds @Singleton abstract fun bindWorkflowReplicaRepository(impl: WorkflowReplicaRepositoryImpl): WorkflowReplicaRepository
    @Binds @Singleton abstract fun bindDeviceReplicaRepository(impl: DeviceReplicaRepositoryImpl): DeviceReplicaRepository
    @Binds @Singleton abstract fun bindCommunicationReplicaRepository(impl: CommunicationReplicaRepositoryImpl): CommunicationReplicaRepository
    @Binds @Singleton abstract fun bindCommunicationGateway(impl: CommunicationGatewayImpl): CommunicationGateway
    @Binds @Singleton abstract fun bindCommunicationSessionRepository(impl: CommunicationRepositoryImpl): CommunicationRepository
    @Binds @Singleton abstract fun bindReplicaMetadataRepository(impl: ReplicaMetadataRepositoryImpl): ReplicaMetadataRepository
    @Binds @Singleton abstract fun bindOutboxRepository(impl: OutboxRepositoryImpl): OutboxRepository
    @Binds @Singleton abstract fun bindPendingEvidenceRepository(impl: PendingEvidenceRepositoryImpl): PendingEvidenceRepository
    @Binds @Singleton abstract fun bindRuntimeStateRepository(impl: RuntimeStateRepositoryImpl): RuntimeStateRepository
    @Binds @Singleton abstract fun bindSynchronizationRepository(impl: SynchronizationRepositoryImpl): SynchronizationRepository
    @Binds @Singleton abstract fun bindSyncSessionLocalRepository(impl: SyncSessionLocalRepositoryImpl): SyncSessionLocalRepository
    @Binds @Singleton abstract fun bindSyncConflictRepository(impl: SyncConflictRepositoryImpl): SyncConflictRepository
    @Binds @Singleton abstract fun bindReplicaSnapshotWriter(impl: ReplicaSnapshotWriterImpl): ReplicaSnapshotWriter
    @Binds @Singleton abstract fun bindSyncApplyTransaction(impl: SyncApplyTransactionImpl): SyncApplyTransaction
    @Binds @Singleton abstract fun bindIntegrationRuntimeRepository(impl: IntegrationRuntimeRepositoryImpl): IntegrationRuntimeRepository
    @Binds @Singleton abstract fun bindHomeRepository(impl: HomeRepositoryImpl): HomeRepository
    @Binds @Singleton abstract fun bindReminderRepository(impl: ReminderRepositoryImpl): ReminderRepository
    @Binds @Singleton abstract fun bindConnectivityRepository(impl: ConnectivityRepositoryImpl): ConnectivityRepository
    @Binds @Singleton abstract fun bindReplicaIdentityProvider(impl: DataStoreReplicaIdentityProvider): ReplicaIdentityProvider
    @Binds @Singleton abstract fun bindCorrelationIdProvider(impl: DataStoreReplicaIdentityProvider): CorrelationIdProvider
}

@Module
@InstallIn(SingletonComponent::class)
abstract class UseCaseModule {
    @Binds abstract fun bindObserveHomeSnapshotUseCase(impl: ObserveHomeSnapshotUseCaseImpl): ObserveHomeSnapshotUseCase
    @Binds abstract fun bindObserveReplicaStateUseCase(impl: ObserveReplicaStateUseCaseImpl): ObserveReplicaStateUseCase
    @Binds abstract fun bindObserveHubIdentityUseCase(impl: ObserveHubIdentityUseCaseImpl): ObserveHubIdentityUseCase
    @Binds abstract fun bindObserveReminderPresentationUseCase(
        impl: ObserveReminderPresentationUseCaseImpl,
    ): ObserveReminderPresentationUseCase
    @Binds abstract fun bindStartSynchronizationUseCase(impl: StartSynchronizationUseCaseImpl): StartSynchronizationUseCase
}

@Module
@InstallIn(SingletonComponent::class)
object AppConfigModule {
    @Provides @IoDispatcher fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO

    @Provides @DefaultDispatcher fun provideDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default
}
