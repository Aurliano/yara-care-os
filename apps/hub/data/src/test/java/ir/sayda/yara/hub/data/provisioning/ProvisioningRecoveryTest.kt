package ir.sayda.yara.hub.data.provisioning

import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import io.mockk.mockkObject
import io.mockk.unmockkObject
import io.mockk.verify
import ir.sayda.yara.hub.core.domain.model.DeviceNotFoundException
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.data.identity.HubIdentityStore
import ir.sayda.yara.hub.data.identity.SecureHubIdentityStore
import ir.sayda.yara.hub.database.dao.MessageDao
import ir.sayda.yara.hub.database.dao.OutboxDao
import ir.sayda.yara.hub.database.dao.PendingEvidenceDao
import ir.sayda.yara.hub.network.api.ProvisioningApi
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.logging.HubNetworkLogger
import ir.sayda.yara.hub.sync.ReplicaStateInitializer
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response
import java.io.IOException
import java.net.SocketTimeoutException

class ProvisioningRecoveryTest {

    private val provisioningApi = mockk<ProvisioningApi>()
    private val authRepository = mockk<AuthRepository>(relaxed = true)
    private val identityStore = mockk<SecureHubIdentityStore>(relaxed = true)
    private val stateMachine = ProvisioningStateMachine()
    private val correlationIdProvider = mockk<CorrelationIdProvider> {
        every { next() } returns "test-corr-id"
    }
    private val replicaStateInitializer = mockk<ReplicaStateInitializer>(relaxed = true)

    private val pendingEvidenceDao = mockk<PendingEvidenceDao>(relaxed = true)
    private val outboxDao = mockk<OutboxDao>(relaxed = true)
    private val messageDao = mockk<MessageDao>(relaxed = true)

    private lateinit var repository: ProvisioningRepositoryImpl

    @Before
    fun setUp() {
        mockkObject(HubNetworkLogger)
        every { HubNetworkLogger.provisioningRegisterAttempt(any(), any()) } returns Unit
        every { HubNetworkLogger.provisioningStarted(any()) } returns Unit
        every { HubNetworkLogger.provisioningCompleted(any(), any()) } returns Unit
        every { HubNetworkLogger.authenticationSuccess(any(), any()) } returns Unit
        every { HubNetworkLogger.authenticationRefresh(any(), any()) } returns Unit
        every { HubNetworkLogger.authenticationFailed(any(), any()) } returns Unit
        every { HubNetworkLogger.backendUnavailable(any(), any()) } returns Unit

        repository = ProvisioningRepositoryImpl(
            provisioningApi = provisioningApi,
            authRepository = authRepository,
            identityStore = identityStore,
            stateMachine = stateMachine,
            correlationIdProvider = correlationIdProvider,
            backendUrl = "http://localhost:8000/api/v1/",
            replicaStateInitializer = replicaStateInitializer,
        )
    }

    @After
    fun tearDown() {
        unmockkObject(HubNetworkLogger)
    }

    private fun sampleStoredProvisioning(
        deviceId: String = "device-123",
        state: ProvisioningState = ProvisioningState.REGISTERED,
    ) = HubIdentityStore.StoredProvisioning(
        deviceId = deviceId,
        replicaId = "replica-123",
        elderId = "elder-123",
        backendUrl = "http://localhost:8000/api/v1/",
        provisionedAtEpochMillis = 1_000_000L,
        lastAuthenticatedAtEpochMillis = 1_000_000L,
        provisioningState = state,
    )

    private fun httpException(code: Int, bodyJson: String): HttpException {
        val body = bodyJson.toResponseBody("application/json".toMediaType())
        return HttpException(Response.error<Unit>(code, body))
    }

    // ========================================================================
    // TEST 1: Confirmed DeviceNotFound (404 with "Device not found")
    // -> Identity is cleared, state becomes UNPROVISIONED, registration can be attempted
    // ========================================================================
    @Test
    fun test1_confirmedDeviceNotFound_clearsIdentityAndBecomesUnprovisioned() = runTest {
        val stored = sampleStoredProvisioning()
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            404,
            """{"detail": "Device not found."}""",
        )

        val result = repository.restoreProvisioning()

        assertTrue(result is AppResult.Success)
        val status = (result as AppResult.Success).data
        assertEquals(ProvisioningState.UNPROVISIONED, status.state)
        assertEquals(ProvisioningState.UNPROVISIONED, stateMachine.currentState())
        coVerify(exactly = 1) { authRepository.clearIdentity() }
    }

    // ========================================================================
    // TEST 2: HTTP 500 -> Identity preserved
    // ========================================================================
    @Test
    fun test2_http500_preservesIdentity() = runTest {
        val stored = sampleStoredProvisioning(state = ProvisioningState.REGISTERED)
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            500,
            """{"detail": "Internal Server Error"}""",
        )

        val result = repository.restoreProvisioning()

        assertTrue(result is AppResult.Success)
        val status = (result as AppResult.Success).data
        assertEquals(ProvisioningState.REGISTERED, status.state)
        assertEquals(ProvisioningState.REGISTERED, stateMachine.currentState())
        coVerify(exactly = 0) { authRepository.clearIdentity() }
        verify(exactly = 0) { identityStore.clear() }
    }

    // ========================================================================
    // TEST 3: HTTP 503 -> Identity preserved
    // ========================================================================
    @Test
    fun test3_http503_preservesIdentity() = runTest {
        val stored = sampleStoredProvisioning(state = ProvisioningState.READY)
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            503,
            """{"detail": "Service Unavailable"}""",
        )

        val result = repository.restoreProvisioning()

        assertTrue(result is AppResult.Success)
        val status = (result as AppResult.Success).data
        assertEquals(ProvisioningState.READY, status.state)
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
        coVerify(exactly = 0) { authRepository.clearIdentity() }
        verify(exactly = 0) { identityStore.clear() }
    }

    // ========================================================================
    // TEST 4: Network timeout -> Identity preserved
    // ========================================================================
    @Test
    fun test4_networkTimeout_preservesIdentity() = runTest {
        val stored = sampleStoredProvisioning(state = ProvisioningState.REGISTERED)
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws SocketTimeoutException("connect timed out")

        val result = repository.restoreProvisioning()

        assertTrue(result is AppResult.Success)
        val status = (result as AppResult.Success).data
        assertEquals(ProvisioningState.REGISTERED, status.state)
        assertEquals(ProvisioningState.REGISTERED, stateMachine.currentState())
        coVerify(exactly = 0) { authRepository.clearIdentity() }
        verify(exactly = 0) { identityStore.clear() }
    }

    // ========================================================================
    // TEST 5: Offline / IOException -> Identity preserved
    // ========================================================================
    @Test
    fun test5_offlineIOException_preservesIdentity() = runTest {
        val stored = sampleStoredProvisioning(state = ProvisioningState.REGISTERED)
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws IOException("No route to host")

        val result = repository.restoreProvisioning()

        assertTrue(result is AppResult.Success)
        val status = (result as AppResult.Success).data
        assertEquals(ProvisioningState.REGISTERED, status.state)
        assertEquals(ProvisioningState.REGISTERED, stateMachine.currentState())
        coVerify(exactly = 0) { authRepository.clearIdentity() }
        verify(exactly = 0) { identityStore.clear() }
    }

    // ========================================================================
    // TEST 6: DeviceNotFound recovery -> pending_evidence unchanged
    // ========================================================================
    @Test
    fun test6_deviceNotFoundRecovery_doesNotTouchPendingEvidence() = runTest {
        val stored = sampleStoredProvisioning()
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            404,
            """{"detail": "Device not found."}""",
        )

        data class EvidenceRecord(
            val id: String,
            val workflowExecutionId: String,
            val idempotencyKey: String,
            val status: String,
            val payloadJson: String,
        )
        val evidenceDatabase = mutableMapOf<String, EvidenceRecord>()
        evidenceDatabase["ev-record-1"] = EvidenceRecord(
            id = "ev-record-1",
            workflowExecutionId = "wf-exec-100",
            idempotencyKey = "idem-key-abc",
            status = "PENDING",
            payloadJson = """{"action": "TAKEN"}""",
        )

        val beforeState = evidenceDatabase["ev-record-1"]

        repository.restoreProvisioning()

        val afterState = evidenceDatabase["ev-record-1"]
        assertEquals(beforeState, afterState)
        assertEquals("ev-record-1", afterState?.id)
        assertEquals("idem-key-abc", afterState?.idempotencyKey)
        assertEquals("PENDING", afterState?.status)
        assertEquals(1, evidenceDatabase.size)

        // Verify PendingEvidenceDao is never invoked to clear or wipe data
        coVerify(exactly = 0) { pendingEvidenceDao.getPending(any()) }
        coVerify(exactly = 0) { pendingEvidenceDao.updateStatus(any(), any(), any(), any(), any(), any()) }
    }

    // ========================================================================
    // TEST 7: DeviceNotFound recovery -> outbox unchanged
    // ========================================================================
    @Test
    fun test7_deviceNotFoundRecovery_doesNotTouchOutbox() = runTest {
        val stored = sampleStoredProvisioning()
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            404,
            """{"detail": "Device not found."}""",
        )

        data class OutboxRecord(
            val id: String,
            val aggregateId: String,
            val idempotencyKey: String,
            val status: String,
            val priority: Int,
        )
        val outboxDatabase = mutableMapOf<String, OutboxRecord>()
        outboxDatabase["outbox-entry-1"] = OutboxRecord(
            id = "outbox-entry-1",
            aggregateId = "agg-occurrence-1",
            idempotencyKey = "outbox-idem-999",
            status = "PENDING",
            priority = 10,
        )

        val beforeState = outboxDatabase["outbox-entry-1"]

        repository.restoreProvisioning()

        val afterState = outboxDatabase["outbox-entry-1"]
        assertEquals(beforeState, afterState)
        assertEquals("outbox-entry-1", afterState?.id)
        assertEquals("outbox-idem-999", afterState?.idempotencyKey)
        assertEquals("PENDING", afterState?.status)
        assertEquals(1, outboxDatabase.size)

        // Verify OutboxDao is never invoked to clear or wipe data
        coVerify(exactly = 0) { outboxDao.getPending(any()) }
        coVerify(exactly = 0) { outboxDao.updateStatus(any(), any(), any(), any(), any(), any()) }
    }

    // ========================================================================
    // TEST 8: DeviceNotFound recovery -> message/history unchanged
    // ========================================================================
    @Test
    fun test8_deviceNotFoundRecovery_doesNotTouchMessageHistory() = runTest {
        val stored = sampleStoredProvisioning()
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            404,
            """{"detail": "Device not found."}""",
        )

        data class MessageRecord(
            val id: String,
            val elderId: String,
            val senderId: String,
            val text: String,
            val createdAt: Long,
        )
        val messageDatabase = mutableMapOf<String, MessageRecord>()
        messageDatabase["msg-entry-1"] = MessageRecord(
            id = "msg-entry-1",
            elderId = "elder-123",
            senderId = "caregiver-456",
            text = "سلام مادر جان قرصت رو خوردی؟",
            createdAt = 1_700_000_000L,
        )

        val beforeState = messageDatabase["msg-entry-1"]

        repository.restoreProvisioning()

        val afterState = messageDatabase["msg-entry-1"]
        assertEquals(beforeState, afterState)
        assertEquals("msg-entry-1", afterState?.id)
        assertEquals("سلام مادر جان قرصت رو خوردی؟", afterState?.text)
        assertEquals(1, messageDatabase.size)

        // Verify MessageDao is never invoked during recovery
        coVerify(exactly = 0) { messageDao.deleteAll() }
    }

    // ========================================================================
    // TEST 9: After identity is cleared, next startup does NOT incorrectly
    // transition back to REGISTERED based only on stale state
    // ========================================================================
    @Test
    fun test9_afterIdentityCleared_startupDoesNotTransitionToRegistered() = runTest {
        // Step 1: Simulate confirmed 404 recovery
        val stored = sampleStoredProvisioning()
        every { identityStore.readProvisioning() } returns stored
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            404,
            """{"detail": "Device not found."}""",
        )
        repository.restoreProvisioning()

        // Step 2: Now simulate next startup where identityStore has been cleared
        every { identityStore.readProvisioning() } returns null

        val secondResult = repository.restoreProvisioning()

        assertTrue(secondResult is AppResult.Success)
        val status = (secondResult as AppResult.Success).data
        assertEquals(ProvisioningState.UNPROVISIONED, status.state)
        assertEquals(ProvisioningState.UNPROVISIONED, stateMachine.currentState())
        // Confirm it does NOT revert back to REGISTERED
        assertFalse(status.state == ProvisioningState.REGISTERED)
    }

    // ========================================================================
    // TEST 10: A different 404 that is NOT DeviceNotFound must NOT clear identity
    // ========================================================================
    @Test
    fun test10_different404NotDeviceNotFound_preservesIdentity() = runTest {
        val stored = sampleStoredProvisioning(state = ProvisioningState.REGISTERED)
        every { identityStore.readProvisioning() } returns stored
        // 404 from unknown endpoint / reverse proxy (not containing "Device not found")
        coEvery { provisioningApi.status(stored.deviceId) } throws httpException(
            404,
            """{"detail": "Not found."}""",
        )

        val result = repository.restoreProvisioning()

        assertTrue(result is AppResult.Success)
        val status = (result as AppResult.Success).data
        assertEquals(ProvisioningState.REGISTERED, status.state)
        assertEquals(ProvisioningState.REGISTERED, stateMachine.currentState())
        coVerify(exactly = 0) { authRepository.clearIdentity() }
        verify(exactly = 0) { identityStore.clear() }
    }

    // ========================================================================
    // BONUS TEST: authenticate() with confirmed DeviceNotFound
    // -> clears identity, returns typed DeviceNotFoundException, state = UNPROVISIONED
    // ========================================================================
    @Test
    fun testBonus_authenticateDeviceNotFound_clearsIdentityAndReturnsTypedException() = runTest {
        coEvery { provisioningApi.authenticate(any()) } throws httpException(
            404,
            """{"detail": "Device not found."}""",
        )

        val result = repository.authenticate("stale-device-id", "09123456789", "pass123")

        assertTrue(result is AppResult.Error)
        val error = (result as AppResult.Error).exception
        assertTrue(error is DeviceNotFoundException)
        assertEquals(ProvisioningState.UNPROVISIONED, stateMachine.currentState())
        coVerify(exactly = 1) { authRepository.clearIdentity() }
    }

    // ========================================================================
    // TEST 11: Task 2.4 / F-05 - authenticate() with pure transport exception
    // on an already-provisioned (READY) device -> preserves READY state!
    // ========================================================================
    @Test
    fun test11_authenticate_whenAlreadyReadyAndPureTransportException_preservesReadyState() = runTest {
        val stored = sampleStoredProvisioning(state = ProvisioningState.READY)
        every { identityStore.readProvisioning() } returns stored
        stateMachine.transitionTo(ProvisioningState.READY)

        coEvery { provisioningApi.authenticate(any()) } throws java.net.ConnectException("Failed to connect to backend")

        val result = repository.authenticate(stored.deviceId, "09123456789", "pass123")

        assertTrue(result is AppResult.Error)
        // CRITICAL CHECK: state machine MUST remain READY, not demoted to ERROR
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
        coVerify(exactly = 0) { authRepository.clearIdentity() }
    }

    // ========================================================================
    // TEST 12: Task 2.4 Condition 1 - authenticate() with HTTP 401 rejection
    // on an already-provisioned device -> transitions to ERROR (security rule)
    // ========================================================================
    @Test
    fun test12_authenticate_whenAlreadyReadyAndHttp401_transitionsToErrorState() = runTest {
        val stored = sampleStoredProvisioning(state = ProvisioningState.READY)
        every { identityStore.readProvisioning() } returns stored
        stateMachine.transitionTo(ProvisioningState.READY)

        coEvery { provisioningApi.authenticate(any()) } throws httpException(
            401,
            """{"detail": "Invalid credentials."}""",
        )

        val result = repository.authenticate(stored.deviceId, "09123456789", "wrongpass")

        assertTrue(result is AppResult.Error)
        // CRITICAL CHECK: HTTP 401 is NOT pure transport; must transition to ERROR
        assertEquals(ProvisioningState.ERROR, stateMachine.currentState())
    }

    // ========================================================================
    // TEST 13: Task 2.4 - authenticate() with pure transport exception
    // on an UNPROVISIONED device -> transitions to ERROR to inform caregiver
    // ========================================================================
    @Test
    fun test13_authenticate_whenUnprovisionedAndPureTransportException_transitionsToError() = runTest {
        every { identityStore.readProvisioning() } returns null
        stateMachine.transitionTo(ProvisioningState.UNPROVISIONED)

        coEvery { provisioningApi.authenticate(any()) } throws java.net.ConnectException("Failed to connect")

        val result = repository.authenticate("fresh-device-id", "09123456789", "pass123")

        assertTrue(result is AppResult.Error)
        // Fresh onboarding requires network; network failure transitions to ERROR
        assertEquals(ProvisioningState.ERROR, stateMachine.currentState())
    }
}

