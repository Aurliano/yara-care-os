package ir.sayda.yara.hub.runtime.di

import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import dagger.multibindings.IntoSet
import ir.sayda.yara.hub.core.domain.usecase.ConfirmReminderUseCase
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.runtime.ActionRegistry
import ir.sayda.yara.hub.core.runtime.RuntimeActionHandler
import ir.sayda.yara.hub.core.runtime.RuntimeDispatcher
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import ir.sayda.yara.hub.core.runtime.RuntimeKernel
import ir.sayda.yara.hub.runtime.component.CommunicationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.DeviceReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.IntegrationRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SchedulingReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.SynchronizationReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.component.WorkflowReplicaRuntimeComponent
import ir.sayda.yara.hub.runtime.dispatcher.ActionDispatcher
import ir.sayda.yara.hub.runtime.dispatcher.DeferredCommunicationActionHandler
import ir.sayda.yara.hub.runtime.dispatcher.DeferredDeviceActionHandler
import ir.sayda.yara.hub.runtime.dispatcher.DefaultActionRegistry
import ir.sayda.yara.hub.runtime.dispatcher.ShowReminderActionHandler
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.kernel.HubRuntimeKernel
import ir.sayda.yara.hub.runtime.usecase.ConfirmReminderUseCaseImpl
import ir.sayda.yara.hub.runtime.usecase.RecoverRuntimeUseCaseImpl
import ir.sayda.yara.hub.runtime.usecase.RunIntegrationCycleUseCaseImpl
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RuntimeModule {
    @Binds @Singleton abstract fun bindRuntimeKernel(impl: HubRuntimeKernel): RuntimeKernel
    @Binds @Singleton abstract fun bindRuntimeDispatcher(impl: ActionDispatcher): RuntimeDispatcher
    @Binds @Singleton abstract fun bindActionRegistry(impl: DefaultActionRegistry): ActionRegistry
    @Binds @Singleton abstract fun bindRuntimeEventBus(impl: RuntimeEventBusImpl): RuntimeEventBus
    @Binds abstract fun bindRunIntegrationCycleUseCase(impl: RunIntegrationCycleUseCaseImpl): RunIntegrationCycleUseCase
    @Binds abstract fun bindRecoverRuntimeUseCase(impl: RecoverRuntimeUseCaseImpl): RecoverRuntimeUseCase
    @Binds abstract fun bindConfirmReminderUseCase(impl: ConfirmReminderUseCaseImpl): ConfirmReminderUseCase

    @Binds @IntoSet abstract fun bindReminderHandler(handler: ShowReminderActionHandler): RuntimeActionHandler
    @Binds @IntoSet abstract fun bindDeviceHandler(handler: DeferredDeviceActionHandler): RuntimeActionHandler
    @Binds @IntoSet abstract fun bindCommunicationHandler(handler: DeferredCommunicationActionHandler): RuntimeActionHandler
}

@Module
@InstallIn(SingletonComponent::class)
object RuntimeComponentModule {
    @Provides @Singleton fun provideSchedulingRuntime(): SchedulingReplicaRuntimeComponent =
        SchedulingReplicaRuntimeComponent()

    @Provides @Singleton fun provideWorkflowRuntime(): WorkflowReplicaRuntimeComponent =
        WorkflowReplicaRuntimeComponent()

    @Provides @Singleton fun provideSynchronizationRuntime(): SynchronizationReplicaRuntimeComponent =
        SynchronizationReplicaRuntimeComponent()

    @Provides @Singleton fun provideDeviceRuntime(): DeviceReplicaRuntimeComponent =
        DeviceReplicaRuntimeComponent()

    @Provides @Singleton fun provideCommunicationRuntime(): CommunicationReplicaRuntimeComponent =
        CommunicationReplicaRuntimeComponent()

    @Provides @Singleton fun provideIntegrationRuntime(): IntegrationRuntimeComponent =
        IntegrationRuntimeComponent()
}
