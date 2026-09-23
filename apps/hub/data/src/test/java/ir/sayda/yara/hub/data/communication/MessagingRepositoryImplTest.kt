package ir.sayda.yara.hub.data.communication

import ir.sayda.yara.hub.core.domain.model.MessageDirection
import ir.sayda.yara.hub.core.domain.model.MessageStatus
import ir.sayda.yara.hub.core.domain.model.MessageType
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.data.media.HubMediaStorage
import ir.sayda.yara.hub.database.dao.ContactDao
import ir.sayda.yara.hub.database.dao.MessageDao
import ir.sayda.yara.hub.database.entity.MessageEntity
import ir.sayda.yara.hub.network.api.CommunicationApi
import ir.sayda.yara.hub.network.dto.MessageResponseDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk

@OptIn(ExperimentalCoroutinesApi::class)
class MessagingRepositoryImplTest {

    private lateinit var messageDao: MessageDao
    private lateinit var contactDao: ContactDao
    private lateinit var communicationApi: CommunicationApi
    private lateinit var outboxRepository: OutboxRepository
    private lateinit var mediaStorage: HubMediaStorage
    private lateinit var repository: MessagingRepositoryImpl

    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setup() {
        messageDao = mockk(relaxed = true)
        contactDao = mockk(relaxed = true)
        communicationApi = mockk(relaxed = true)
        outboxRepository = mockk(relaxed = true)
        mediaStorage = mockk(relaxed = true)

        repository = MessagingRepositoryImpl(
            messageDao = messageDao,
            contactDao = contactDao,
            communicationApi = communicationApi,
            outboxRepository = outboxRepository,
            mediaStorage = mediaStorage,
            ioDispatcher = testDispatcher
        )
    }

    @Test
    fun `syncElderMessages does not upsert if message is identical`() = runTest(testDispatcher) {
        val elderId = "elder-1"
        val messageId = "msg-1"
        
        val dto = MessageResponseDto(
            id = messageId,
            elderId = elderId,
            direction = "HUB_TO_FAMILY",
            messageType = "TEXT",
            body = "Hello",
            attachment = null,
            status = "SENT",
            idempotencyKey = "key1",
            createdAt = "2026-09-12T10:00:00Z",
            deliveredAt = null,
            readAt = null,
            sender = null,
            senderDisplayName = "Hub"
        )
        
        coEvery { communicationApi.getMessages(elderId, any(), any()) } returns listOf(dto)
        
        val existingEntity = MessageEntity(
            id = messageId,
            elderId = elderId,
            direction = MessageDirection.HUB_TO_FAMILY.name,
            messageType = MessageType.TEXT.name,
            body = "Hello",
            attachmentId = null,
            localFileUri = null,
            durationSeconds = null,
            fileSize = null,
            status = MessageStatus.SENT.name,
            idempotencyKey = "key1",
            createdAtEpochMillis = java.time.Instant.parse("2026-09-12T10:00:00Z").toEpochMilli(),
            deliveredAtEpochMillis = null,
            readAtEpochMillis = null,
            senderDisplayName = "Hub"
        )
        
        coEvery { messageDao.getById(messageId) } returns existingEntity
        
        val result = repository.syncElderMessages(elderId)
        
        assertTrue(result is AppResult.Success)
        assertEquals(1, (result as AppResult.Success).data)
        
        // Ensure getById was called to check
        coVerify(exactly = 1) { messageDao.getById(messageId) }
        
        // Ensure upsert was NOT called because they are identical
        coVerify(exactly = 0) { messageDao.upsert(any()) }
    }

    // M-RENDER regression: a FAMILY_TO_HUB message that is already DELIVERED locally
    // must NOT trigger another markDelivered call (which would cause a DB write →
    // Room Flow emit → unnecessary UI recomposition on every 3-second poll).
    @Test
    fun `syncElderMessages does not call markDelivered if message is already DELIVERED locally`() = runTest(testDispatcher) {
        val elderId = "elder-2"
        val messageId = "msg-delivered"

        val dto = MessageResponseDto(
            id = messageId,
            elderId = elderId,
            direction = "FAMILY_TO_HUB",
            messageType = "TEXT",
            body = "Hi from family",
            attachment = null,
            // Remote DTO still reports SENT (hasn't been updated on backend yet)
            status = "SENT",
            idempotencyKey = "key-delivered",
            createdAt = "2026-09-12T11:00:00Z",
            deliveredAt = null,
            readAt = null,
            sender = null,
            senderDisplayName = "Family"
        )

        coEvery { communicationApi.getMessages(elderId, any(), any()) } returns listOf(dto)

        // Locally the message is already DELIVERED (higher priority than SENT)
        val existingDeliveredEntity = MessageEntity(
            id = messageId,
            elderId = elderId,
            direction = MessageDirection.FAMILY_TO_HUB.name,
            messageType = MessageType.TEXT.name,
            body = "Hi from family",
            attachmentId = null,
            localFileUri = null,
            durationSeconds = null,
            fileSize = null,
            status = MessageStatus.DELIVERED.name,
            idempotencyKey = "key-delivered",
            createdAtEpochMillis = java.time.Instant.parse("2026-09-12T11:00:00Z").toEpochMilli(),
            deliveredAtEpochMillis = System.currentTimeMillis() - 5000,
            readAtEpochMillis = null,
            senderDisplayName = "Family"
        )

        coEvery { messageDao.getById(messageId) } returns existingDeliveredEntity

        val result = repository.syncElderMessages(elderId)

        assertTrue(result is AppResult.Success)
        // markDelivered must NOT be called — the resolved status is DELIVERED, not SENT
        coVerify(exactly = 0) { communicationApi.markDelivered(any()) }
        // updateStatus must NOT be called for delivery (no redundant DB write)
        coVerify(exactly = 0) { messageDao.updateStatus(messageId, MessageStatus.DELIVERED.name, any(), any()) }
    }

    // M-READ regression: a FAMILY_TO_HUB message that was READ locally must retain
    // READ status even when the remote DTO reports a lower-priority status (SENT).
    @Test
    fun `syncElderMessages preserves READ status when remote DTO reports SENT`() = runTest(testDispatcher) {
        val elderId = "elder-3"
        val messageId = "msg-read"

        val dto = MessageResponseDto(
            id = messageId,
            elderId = elderId,
            direction = "FAMILY_TO_HUB",
            messageType = "TEXT",
            body = "Hello read message",
            attachment = null,
            // Backend still says SENT (read acknowledgement may not have propagated)
            status = "SENT",
            idempotencyKey = "key-read",
            createdAt = "2026-09-12T12:00:00Z",
            deliveredAt = null,
            readAt = null,
            sender = null,
            senderDisplayName = "Family"
        )

        coEvery { communicationApi.getMessages(elderId, any(), any()) } returns listOf(dto)

        val existingReadEntity = MessageEntity(
            id = messageId,
            elderId = elderId,
            direction = MessageDirection.FAMILY_TO_HUB.name,
            messageType = MessageType.TEXT.name,
            body = "Hello read message",
            attachmentId = null,
            localFileUri = null,
            durationSeconds = null,
            fileSize = null,
            status = MessageStatus.READ.name,
            idempotencyKey = "key-read",
            createdAtEpochMillis = java.time.Instant.parse("2026-09-12T12:00:00Z").toEpochMilli(),
            deliveredAtEpochMillis = System.currentTimeMillis() - 10000,
            readAtEpochMillis = System.currentTimeMillis() - 5000,
            senderDisplayName = "Family"
        )

        coEvery { messageDao.getById(messageId) } returns existingReadEntity

        val result = repository.syncElderMessages(elderId)

        assertTrue(result is AppResult.Success)
        // READ status (priority 3) is higher than SENT (priority 1) — must be preserved
        // markDelivered must NOT be called for an already-READ message
        coVerify(exactly = 0) { communicationApi.markDelivered(any()) }
    }

    // M1-B regression: Outgoing HUB_TO_FAMILY message created with a temporary client ID
    // must reconcile by idempotencyKey upon sync, preserving localFileUri and removing the temp ID.
    @Test
    fun `syncElderMessages reconciles entity by idempotencyKey when client ID differs from backend UUID`() = runTest(testDispatcher) {
        val elderId = "elder-4"
        val serverMessageId = "server-uuid-123"
        val clientMessageId = "client-temp-uuid-456"
        val idempotencyKey = "idem-voice-001"
        val localFilePath = "/data/user/0/ir.sayda.yara.hub/cache/voice.m4a"

        val dto = MessageResponseDto(
            id = serverMessageId,
            elderId = elderId,
            direction = "HUB_TO_FAMILY",
            messageType = "VOICE",
            body = null,
            attachment = null,
            status = "SENT",
            idempotencyKey = idempotencyKey,
            createdAt = "2026-09-12T13:00:00Z",
            deliveredAt = null,
            readAt = null,
            sender = null,
            senderDisplayName = "خانه"
        )

        coEvery { communicationApi.getMessages(elderId, any(), any()) } returns listOf(dto)
        // messageDao.getById(serverMessageId) returns null
        coEvery { messageDao.getById(serverMessageId) } returns null
        // messageDao.getByIdempotencyKey(idempotencyKey) returns the locally originated entity
        val localEntity = MessageEntity(
            id = clientMessageId,
            elderId = elderId,
            direction = MessageDirection.HUB_TO_FAMILY.name,
            messageType = MessageType.VOICE.name,
            body = null,
            attachmentId = null,
            localFileUri = localFilePath,
            durationSeconds = 5,
            fileSize = 12345L,
            status = MessageStatus.SENT.name,
            idempotencyKey = idempotencyKey,
            createdAtEpochMillis = java.time.Instant.parse("2026-09-12T13:00:00Z").toEpochMilli(),
            deliveredAtEpochMillis = null,
            readAtEpochMillis = null,
            senderDisplayName = "خانه"
        )
        coEvery { messageDao.getByIdempotencyKey(idempotencyKey) } returns localEntity

        val result = repository.syncElderMessages(elderId)

        assertTrue(result is AppResult.Success)
        assertEquals(1, (result as AppResult.Success).data)

        // Temporary client ID row must be deleted
        coVerify(exactly = 1) { messageDao.deleteById(clientMessageId) }

        // Upserted entity must use server ID while preserving localFileUri
        coVerify {
            messageDao.upsert(match {
                it.id == serverMessageId &&
                    it.localFileUri == localFilePath &&
                    it.idempotencyKey == idempotencyKey
            })
        }
    }

    // M1-A regression: markMessageRead updates DAO to READ and acknowledges to backend
    @Test
    fun `markMessageRead updates DAO to READ and notifies backend`() = runTest(testDispatcher) {
        val messageId = "msg-to-mark-read"

        val result = repository.markMessageRead(messageId)

        assertTrue(result is AppResult.Success)
        coVerify(exactly = 1) {
            messageDao.updateStatus(
                id = messageId,
                status = MessageStatus.READ.name,
                deliveredAt = any(),
                readAt = any()
            )
        }
        coVerify(exactly = 1) { communicationApi.markRead(messageId) }
    }
}

