package ir.sayda.yara.hub.network.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import ir.sayda.yara.hub.core.di.HubBaseUrl
import ir.sayda.yara.hub.core.di.ProvisioningClient
import ir.sayda.yara.hub.core.di.UnauthenticatedAuth
import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.api.HubIntegrationApi
import ir.sayda.yara.hub.network.api.ProvisioningApi
import ir.sayda.yara.hub.network.auth.TokenRefreshHandler
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.identity.ReplicaIdentityProvider
import ir.sayda.yara.hub.network.interceptor.AuthInterceptor
import ir.sayda.yara.hub.network.interceptor.HubHeadersInterceptor
import ir.sayda.yara.hub.network.interceptor.TokenAuthenticator
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        explicitNulls = false
    }

    @Provides
    @Singleton
    fun provideJson(): Json = json

    @Provides
    @Singleton
    @ProvisioningClient
    fun provideProvisioningOkHttpClient(
        correlationIdProvider: CorrelationIdProvider,
    ): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val correlationInterceptor = okhttp3.Interceptor { chain ->
            val request = chain.request().newBuilder()
                .header("X-Correlation-ID", correlationIdProvider.next())
                .build()
            chain.proceed(request)
        }
        return OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .addInterceptor(correlationInterceptor)
            .addInterceptor(logging)
            .build()
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        hubHeadersInterceptor: HubHeadersInterceptor,
        tokenAuthenticator: TokenAuthenticator,
    ): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        return OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(hubHeadersInterceptor)
            .addInterceptor(authInterceptor)
            .authenticator(tokenAuthenticator)
            .addInterceptor(logging)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(
        @HubBaseUrl baseUrl: String,
        okHttpClient: OkHttpClient,
    ): Retrofit {
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
    }

    @Provides
    @Singleton
    fun provideAuthApi(retrofit: Retrofit): AuthApi = retrofit.create(AuthApi::class.java)

    @Provides
    @Singleton
    @UnauthenticatedAuth
    fun provideUnauthenticatedAuthApi(
        @HubBaseUrl baseUrl: String,
        @ProvisioningClient okHttpClient: OkHttpClient,
    ): AuthApi {
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
            .create(AuthApi::class.java)
    }

    @Provides
    @Singleton
    fun provideHubIntegrationApi(retrofit: Retrofit): HubIntegrationApi =
        retrofit.create(HubIntegrationApi::class.java)

    @Provides
    @Singleton
    fun provideSynchronizationDomainApi(retrofit: Retrofit): ir.sayda.yara.hub.network.api.SynchronizationDomainApi =
        retrofit.create(ir.sayda.yara.hub.network.api.SynchronizationDomainApi::class.java)

    @Provides
    @Singleton
    fun provideProvisioningApi(
        @HubBaseUrl baseUrl: String,
        @ProvisioningClient okHttpClient: OkHttpClient,
    ): ProvisioningApi {
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
            .create(ProvisioningApi::class.java)
    }

    @Provides
    @Singleton
    fun provideCommunicationApi(retrofit: Retrofit): ir.sayda.yara.hub.network.api.CommunicationApi =
        retrofit.create(ir.sayda.yara.hub.network.api.CommunicationApi::class.java)

    @Provides
    @Singleton
    fun provideTokenAuthenticator(
        tokenRefreshHandler: dagger.Lazy<TokenRefreshHandler>,
    ): TokenAuthenticator = TokenAuthenticator(tokenRefreshHandler)

    @Provides
    @Singleton
    fun provideAuthInterceptor(identityProvider: ReplicaIdentityProvider): AuthInterceptor =
        AuthInterceptor(identityProvider)

    @Provides
    @Singleton
    fun provideHubHeadersInterceptor(
        identityProvider: ReplicaIdentityProvider,
        correlationIdProvider: CorrelationIdProvider,
    ): HubHeadersInterceptor = HubHeadersInterceptor(identityProvider, correlationIdProvider)
}
