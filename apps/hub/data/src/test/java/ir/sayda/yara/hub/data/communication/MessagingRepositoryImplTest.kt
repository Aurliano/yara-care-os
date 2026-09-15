package ir.sayda.yara.hub.data.communication

import ir.sayda.yara.hub.core.domain.model.MessageDirection
import ir.sayda.yara.hub.core.domain.model.MessageStatus
import ir.sayda.yara.hub.core.domain.model.MessageType
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.data.media.HubMediaStorage
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
    private lateinit var communicationApi: CommunicationApi
    private lateinit var outboxRepository: OutboxRepository
    private lateinit var mediaStorage: HubMediaStorage
    private lateinit var repository: MessagingRepositoryImpl

    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setup() {
        messageDao = mockk(relaxed = true)
        communicationApi = mockk(relaxed = true)
        outboxRepository = mockk(relaxed = true)
        mediaStorage = mockk(relaxed = true)

        repository = MessagingRepositoryImpl(
            messageDao = messageDao,
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
}
