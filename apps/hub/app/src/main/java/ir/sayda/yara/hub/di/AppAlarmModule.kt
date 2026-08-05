package ir.sayda.yara.hub.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.alarm.AlarmRegistry
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmRegistry
import ir.sayda.yara.hub.core.runtime.ReminderNotificationGateway
import ir.sayda.yara.hub.notification.ReminderNotificationGatewayImpl
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class AppAlarmModule {
    @Binds
    @Singleton
    abstract fun bindOccurrenceAlarmRegistry(impl: AlarmRegistry): OccurrenceAlarmRegistry

    @Binds
    @Singleton
    abstract fun bindReminderNotificationGateway(
        impl: ReminderNotificationGatewayImpl,
    ): ReminderNotificationGateway
}
