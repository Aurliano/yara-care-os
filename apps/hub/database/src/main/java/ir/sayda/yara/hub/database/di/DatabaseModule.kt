package ir.sayda.yara.hub.database.di

import android.content.Context
import androidx.room.Room
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.migration.MIGRATION_1_2
import ir.sayda.yara.hub.database.migration.MIGRATION_2_3
import ir.sayda.yara.hub.database.migration.MIGRATION_3_4
import ir.sayda.yara.hub.database.migration.MIGRATION_4_5
import ir.sayda.yara.hub.database.migration.MIGRATION_5_6
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideHubDatabase(@ApplicationContext context: Context): HubDatabase =
        Room.databaseBuilder(
            context,
            HubDatabase::class.java,
            "yara_hub.db",
        ).addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5, MIGRATION_5_6)
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    @Singleton
    fun provideMessageDao(database: HubDatabase): ir.sayda.yara.hub.database.dao.MessageDao =
        database.messageDao()
}
