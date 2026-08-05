package ir.sayda.yara.hub.network.api

import ir.sayda.yara.hub.network.dto.HubConfirmationRequestDto
import ir.sayda.yara.hub.network.dto.HubConfirmationResponseDto
import ir.sayda.yara.hub.network.dto.HubRuntimeProcessResponseDto
import ir.sayda.yara.hub.network.dto.HubSyncOperationResponseDto
import ir.sayda.yara.hub.network.dto.HubSyncPayloadRequestDto
import ir.sayda.yara.hub.network.dto.HubSyncStartRequestDto
import ir.sayda.yara.hub.network.dto.HubSyncStartResponseDto
import ir.sayda.yara.hub.network.dto.TokenRefreshRequestDto
import ir.sayda.yara.hub.network.dto.TokenRequestDto
import ir.sayda.yara.hub.network.dto.TokenResponseDto
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Path

interface AuthApi {
    @POST("auth/token/")
    suspend fun obtainToken(@Body body: TokenRequestDto): TokenResponseDto

    @POST("auth/token/refresh/")
    suspend fun refreshToken(@Body body: TokenRefreshRequestDto): TokenResponseDto
}

interface HubIntegrationApi {
    @POST("hub/runtime/process/")
    suspend fun processRuntime(): HubRuntimeProcessResponseDto

    @POST("hub/confirmations/")
    suspend fun submitConfirmation(@Body body: HubConfirmationRequestDto): HubConfirmationResponseDto

    @POST("hub/sync/start/")
    suspend fun startSync(@Body body: HubSyncStartRequestDto): HubSyncStartResponseDto

    @POST("hub/sync/sessions/{sessionId}/delta/")
    suspend fun submitDelta(
        @Path("sessionId") sessionId: String,
        @Body body: HubSyncPayloadRequestDto,
    ): HubSyncOperationResponseDto

    @POST("hub/sync/sessions/{sessionId}/snapshot/")
    suspend fun submitSnapshot(
        @Path("sessionId") sessionId: String,
        @Body body: HubSyncPayloadRequestDto,
    ): HubSyncOperationResponseDto
}
