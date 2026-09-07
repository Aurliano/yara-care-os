package ir.sayda.yara.hub.data.communication

import ir.sayda.yara.hub.core.di.IoDispatcher
import ir.sayda.yara.hub.core.domain.model.Message
import ir.sayda.yara.hub.core.domain.model.MessageDirection
import ir.sayda.yara.hub.core.domain.model.MessageStatus
import ir.sayda.yara.hub.core.domain.model.MessageType
import ir.sayda.yara.hub.core.domain.repository.MessagingRepository
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.OutboxOperationType
import ir.sayda.yara.hub.data.media.HubMediaStorage
import ir.sayda.yara.hub.database.dao.MessageDao
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import ir.sayda.yara.hub.network.api.CommunicationApi
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import ir.sayda.yara.hub.network.dto.SendMessageRequestDto
import java.io.File
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MessagingRepositoryImpl @Inject constructor(
    private val messageDao: MessageDao,
    private val communicationApi: CommunicationApi,
    private val outboxRepository: OutboxRepository,
    private val mediaStorage: HubMediaStorage,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher,
) : MessagingRepository {

    override fun observeMessages(elderId: String): Flow<List<Message>> =
        messageDao.observeByElder(elderId).map { list -> list.map { it.toDomain() } }

    override fun observeUnreadCount(elderId: String): Flow<Int> =
        messageDao.observeUnreadCount(elderId)

    override suspend fun getMessage(id: String): Message? = withContext(ioDispatcher) {
        messageDao.getById(id)?.toDomain()
    }

    override suspend fun saveMessage(message: Message): Unit = withContext(ioDispatcher) {
        messageDao.upsert(message.toEntity())
    }

    override suspend fun updateMessageStatus(
        id: String,
        status: MessageStatus,
        deliveredAt: Long?,
        readAt: Long?,
    ): Unit = withContext(ioDispatcher) {
        messageDao.updateStatus(id, status.name, deliveredAt, readAt)
    }

    override suspend fun getPendingOutgoingMessages(): List<Message> = withContext(ioDispatcher) {
        messageDao.getPendingOutgoing().map { it.toDomain() }
    }

    override suspend fun markMessageDelivered(id: String): AppResult<Unit> = withContext(ioDispatcher) {
        try {
            messageDao.updateStatus(
                id = id,
                status = MessageStatus.DELIVERED.name,
                deliveredAt = System.currentTimeMillis(),
                readAt = null,
            )
            runCatching { communicationApi.markDelivered(id) }
            AppResult.Success(Unit)
        } catch (e: Exception) {
            AppResult.Error(e)
        }
    }

    override suspend fun markMessageRead(id: String): AppResult<Unit> = withContext(ioDispatcher) {
        try {
            val now = System.currentTimeMillis()
            messageDao.updateStatus(
                id = id,
                status = MessageStatus.READ.name,
                deliveredAt = now,
                readAt = now,
            )
            runCatching { communicationApi.markRead(id) }
            AppResult.Success(Unit)
        } catch (e: Exception) {
            AppResult.Error(e)
        }
    }

    override suspend fun enqueueOutgoingMessage(
        elderId: String,
        messageType: MessageType,
        body: String?,
        localFileUri: String?,
        durationSeconds: Int?,
        fileSize: Long?,
    ): AppResult<Message> = withContext(ioDispatcher) {
        try {
            val messageId = UUID.randomUUID().toString()
            val idempotencyKey = UUID.randomUUID().toString()
            val now = System.currentTimeMillis()

            val message = Message(
                id = messageId,
                elderId = elderId,
                direction = MessageDirection.HUB_TO_FAMILY,
                messageType = messageType,
                body = body,
                attachmentId = null,
                localFileUri = localFileUri,
                durationSeconds = durationSeconds,
                fileSize = fileSize,
                status = MessageStatus.PENDING,
                idempotencyKey = idempotencyKey,
                createdAtEpochMillis = now,
                senderDisplayName = "خانه",
            )

            messageDao.upsert(message.toEntity())

            val payloadJson = buildJsonObject {
                put("message_id", messageId)
                put("elder_id", elderId)
                put("message_type", messageType.name)
                body?.let { put("body", it) }
                localFileUri?.let { put("local_file_uri", it) }
                durationSeconds?.let { put("duration_seconds", it) }
                fileSize?.let { put("file_size", it) }
                put("idempotency_key", idempotencyKey)
            }.toString()

            outboxRepository.enqueue(
                operationType = OutboxOperationType.SEND_MESSAGE,
                payloadJson = payloadJson,
                idempotencyKey = idempotencyKey,
                priority = 1,
            )

            // Attempt immediate dispatch if network is available
            try {
                val dispatchResult = dispatchOutboxMessage(payloadJson, idempotencyKey)
                if (dispatchResult is AppResult.Success) {
                    val pending = outboxRepository.getPendingEntries(10)
                    pending.firstOrNull { it.idempotencyKey == idempotencyKey }?.let {
                        outboxRepository.markCompleted(it.id)
                    }
                }
            } catch (_: Exception) {
                // Background sync worker will retry
            }

            AppResult.Success(message)
        } catch (e: Exception) {
            AppResult.Error(e)
        }
    }

    override suspend fun dispatchOutboxMessage(payloadJson: String, idempotencyKey: String): AppResult<Unit> = withContext(ioDispatcher) {
        try {
            val element = Json.parseToJsonElement(payloadJson).jsonObject
            val messageId = element["message_id"]?.jsonPrimitive?.content
                ?: return@withContext AppResult.Error(IllegalArgumentException("Missing message_id in payload"))
            val elderId = element["elder_id"]?.jsonPrimitive?.content
                ?: return@withContext AppResult.Error(IllegalArgumentException("Missing elder_id in payload"))
            val messageType = element["message_type"]?.jsonPrimitive?.content ?: "TEXT"
            val body = element["body"]?.jsonPrimitive?.content
            val localFileUri = element["local_file_uri"]?.jsonPrimitive?.content

            var attachmentId: String? = null
            if (localFileUri != null) {
                val file = File(localFileUri)
                if (file.exists()) {
                    val mimeType = when (messageType.uppercase()) {
                        "VOICE" -> "audio/mp4"
                        "IMAGE" -> "image/jpeg"
                        "VIDEO" -> "video/mp4"
                        else -> "application/octet-stream"
                    }
                    val requestFile = file.asRequestBody(mimeType.toMediaTypeOrNull())
                    val filePart = MultipartBody.Part.createFormData("file", file.name, requestFile)
                    val mediaTypeBody = messageType.uppercase().toRequestBody("text/plain".toMediaTypeOrNull())
                    val uploadResponse = communicationApi.uploadMedia(filePart, mediaTypeBody)
                    attachmentId = uploadResponse.id
                }
            }

            val request = SendMessageRequestDto(
                direction = "HUB_TO_FAMILY",
                messageType = messageType.uppercase(),
                body = body,
                attachmentId = attachmentId,
                idempotencyKey = idempotencyKey,
            )
            communicationApi.sendMessage(elderId = elderId, body = request)
            messageDao.updateStatus(
                id = messageId,
                status = MessageStatus.SENT.name,
                deliveredAt = null,
                readAt = null,
            )
            AppResult.Success(Unit)
        } catch (e: Exception) {
            AppResult.Error(e)
        }
    }

    private var lastSyncEpochMillis: Long? = null

    override suspend fun syncElderMessages(elderId: String): AppResult<Int> = withContext(ioDispatcher) {
        try {
            val sinceParam = lastSyncEpochMillis?.let { (it - 10_000L).coerceAtLeast(0L) }
            val remoteMessages = communicationApi.getMessages(elderId = elderId, since = sinceParam, limit = 50)
            if (remoteMessages.isNotEmpty()) {
                val maxCreated = remoteMessages.mapNotNull {
                    runCatching { java.time.Instant.parse(it.createdAt).toEpochMilli() }.getOrNull()
                }.maxOrNull()
                if (maxCreated != null && (lastSyncEpochMillis == null || maxCreated > lastSyncEpochMillis!!)) {
                    lastSyncEpochMillis = maxCreated
                }
            }
            var count = 0
            for (dto in remoteMessages) {
                val existing = messageDao.getById(dto.id)
                var localFileUri = existing?.localFileUri

                val attachment = dto.attachment
                // If message has an attachment and no local file yet, download it
                if (attachment != null && attachment.id.isNotBlank() && localFileUri == null) {
                    try {
                        val responseBody = communicationApi.downloadMedia(attachment.id)
                        val ext = when (attachment.mediaType?.uppercase()) {
                            "VOICE" -> "m4a"
                            "IMAGE" -> "jpg"
                            "VIDEO" -> "mp4"
                            else -> when {
                                attachment.mimeType.contains("audio") -> "m4a"
                                attachment.mimeType.contains("image") -> "jpg"
                                attachment.mimeType.contains("video") -> "mp4"
                                else -> "bin"
                            }
                        }
                        val savedFile = mediaStorage.saveIncomingMedia(
                            attachmentId = attachment.id,
                            extension = ext,
                            inputStream = responseBody.byteStream(),
                        )
                        localFileUri = savedFile.absolutePath
                    } catch (_: Exception) {
                        // Download will retry on next sync if needed
                    }
                }

                val direction = runCatching {
                    MessageDirection.valueOf(dto.direction.uppercase())
                }.getOrDefault(MessageDirection.FAMILY_TO_HUB)

                val messageType = runCatching {
                    MessageType.valueOf(dto.messageType.uppercase())
                }.getOrDefault(MessageType.TEXT)

                val status = runCatching {
                    MessageStatus.valueOf(dto.status.uppercase())
                }.getOrDefault(MessageStatus.SENT)

                val message = Message(
                    id = dto.id,
                    elderId = dto.elderId,
                    direction = direction,
                    messageType = messageType,
                    body = dto.body,
                    attachmentId = attachment?.id,
                    localFileUri = localFileUri,
                    durationSeconds = attachment?.durationSeconds?.toInt(),
                    fileSize = attachment?.fileSize,
                    status = status,
                    idempotencyKey = dto.idempotencyKey,
                    createdAtEpochMillis = runCatching {
                        java.time.Instant.parse(dto.createdAt).toEpochMilli()
                    }.getOrDefault(System.currentTimeMillis()),
                    deliveredAtEpochMillis = dto.deliveredAt?.let {
                        runCatching { java.time.Instant.parse(it).toEpochMilli() }.getOrNull()
                    },
                    readAtEpochMillis = dto.readAt?.let {
                        runCatching { java.time.Instant.parse(it).toEpochMilli() }.getOrNull()
                    },
                    senderDisplayName = dto.sender?.displayName ?: dto.senderDisplayName ?: "خانواده",
                )

                messageDao.upsert(message.toEntity())

                // If this is an incoming family message and not delivered yet, mark delivered
                if (direction == MessageDirection.FAMILY_TO_HUB && status == MessageStatus.SENT) {
                    runCatching {
                        communicationApi.markDelivered(dto.id)
                        messageDao.updateStatus(
                            id = dto.id,
                            status = MessageStatus.DELIVERED.name,
                            deliveredAt = System.currentTimeMillis(),
                        )
                    }
                }
                count++
            }
            AppResult.Success(count)
        } catch (e: Exception) {
            AppResult.Error(e)
        }
    }
}
