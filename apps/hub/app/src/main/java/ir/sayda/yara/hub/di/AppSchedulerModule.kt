package ir.sayda.yara.hub.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.scheduler.WorkManagerRuntimeScheduler
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class AppSchedulerModule {
    @Binds
    @Singleton
    abstract fun bindRuntimeScheduler(impl: WorkManagerRuntimeScheduler): RuntimeScheduler
}
