package ir.sayda.yara.hub.sync.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.core.sync.SynchronizationClient
import ir.sayda.yara.hub.sync.SynchronizationClientImpl
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class SyncModule {
    @Binds
    @Singleton
    abstract fun bindSynchronizationClient(impl: SynchronizationClientImpl): SynchronizationClient
}
