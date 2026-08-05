package ir.sayda.yara.hub.sync.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.sync.SynchronizationClient
import ir.sayda.yara.hub.sync.SynchronizationClientImpl
import ir.sayda.yara.hub.sync.usecase.RunSynchronizationCycleUseCaseImpl
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class SyncModule {
    @Binds
    @Singleton
    abstract fun bindSynchronizationClient(impl: SynchronizationClientImpl): SynchronizationClient

    @Binds
    abstract fun bindRunSynchronizationCycleUseCase(
        impl: RunSynchronizationCycleUseCaseImpl,
    ): RunSynchronizationCycleUseCase
}
