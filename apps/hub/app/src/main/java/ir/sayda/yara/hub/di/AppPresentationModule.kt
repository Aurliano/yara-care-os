package ir.sayda.yara.hub.app.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.presentation.CommunicationPresentationGatewayImpl
import ir.sayda.yara.hub.presentation.ReminderPresentationGatewayImpl
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import ir.sayda.yara.hub.core.runtime.ReminderPresentationGateway
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class AppPresentationModule {
    @Binds
    @Singleton
    abstract fun bindReminderPresentationGateway(
        impl: ReminderPresentationGatewayImpl,
    ): ReminderPresentationGateway

    @Binds
    @Singleton
    abstract fun bindCommunicationPresentationGateway(
        impl: CommunicationPresentationGatewayImpl,
    ): CommunicationPresentationGateway
}
