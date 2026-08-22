package ir.sayda.yara.hub.data.communication

import ir.sayda.yara.hub.core.communication.ActiveCallExistsException
import ir.sayda.yara.hub.core.communication.CommunicationGateway
import ir.sayda.yara.hub.core.communication.CommunicationProviderException
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.network.api.CommunicationApi
import ir.sayda.yara.hub.network.dto.CallEndRequestDto
import ir.sayda.yara.hub.network.dto.CallJoinResponseDto
import ir.sayda.yara.hub.network.dto.CallJoinTokenRequestDto
import ir.sayda.yara.hub.network.dto.CallStartRequestDto
import retrofit2.HttpException
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CommunicationGatewayImpl @Inject constructor(
    private val communicationApi: CommunicationApi,
) : CommunicationGateway {

    override suspend fun startCall(
        elderId: String,
        channel: String,
        recipientContactId: String,
    ): AppResult<CallSession> {
        return try {
            val dto = communicationApi.startCall(
                CallStartRequestDto(
                    elderId = elderId,
                    channel = channel,
                    recipientContactId = recipientContactId,
                ),
            )
            val sessionId = dto.sessionId
                ?: return AppResult.Error(IllegalStateException("Backend startCall did not return sessionId."))
            AppResult.Success(
                dto.toCallSession(
                    sessionId = sessionId,
                    elderId = elderId,
                    channel = channel,
                    recipientContactId = recipientContactId,
                ),
            )
        } catch (exception: HttpException) {
            AppResult.Error(mapHttpException(exception))
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun endCall(sessionId: String): AppResult<Unit> {
        return try {
            communicationApi.endCall(CallEndRequestDto(sessionId = sessionId))
            AppResult.Success(Unit)
        } catch (exception: HttpException) {
            AppResult.Error(mapHttpException(exception))
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun refreshJoinToken(elderId: String): AppResult<CallSession> {
        return try {
            val dto = communicationApi.refreshJoinToken(CallJoinTokenRequestDto(elderId = elderId))
            AppResult.Success(
                dto.toCallSession(
                    sessionId = dto.sessionId.orEmpty(),
                    elderId = elderId,
                    channel = "",
                    recipientContactId = "",
                ),
            )
        } catch (exception: HttpException) {
            AppResult.Error(mapHttpException(exception))
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    private fun mapHttpException(exception: HttpException): Throwable {
        if (exception.code() == 409) {
            return ActiveCallExistsException()
        }
        if (exception.code() == 502) {
            val body = readErrorBody(exception)
            val detail = readJsonField(body, "detail").ifBlank { exception.message().orEmpty() }
            if (detail.isNotBlank()) {
                return CommunicationProviderException(detail, reason = readJsonField(body, "reason"))
            }
        }
        return exception
    }
}

internal fun CallJoinResponseDto.toCallSession(
    sessionId: String,
    elderId: String,
    channel: String,
    recipientContactId: String,
    nowMillis: Long = System.currentTimeMillis(),
): CallSession = CallSession(
    sessionId = sessionId,
    elderId = elderId,
    channel = channel,
    recipientContactId = recipientContactId,
    runtimeState = CallRuntimeState.Connecting,
    joinToken = joinToken,
    expiresAtEpochMillis = parseExpiresAt(expiresAt, nowMillis),
    updatedAtEpochMillis = nowMillis,
)

internal fun parseExpiresAt(value: String, fallbackNow: Long): Long =
    runCatching { Instant.parse(value).toEpochMilli() }.getOrDefault(fallbackNow + DEFAULT_JOIN_TTL_MS)

private fun readErrorBody(exception: HttpException): String =
    runCatching { exception.response()?.errorBody()?.string().orEmpty() }.getOrDefault("")

private fun readJsonField(body: String, field: String): String =
    body.substringAfter("\"$field\":\"", missingDelimiterValue = "")
        .substringBefore("\"")
        .replace("\\u0027", "'")
        .replace("\\\"", "\"")

private const val DEFAULT_JOIN_TTL_MS = 3_600_000L
