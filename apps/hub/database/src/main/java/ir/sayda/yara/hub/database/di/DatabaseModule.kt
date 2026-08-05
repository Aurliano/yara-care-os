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
        ).addMigrations(MIGRATION_1_2)
            .fallbackToDestructiveMigration()
            .build()
}
