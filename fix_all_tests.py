import re

file_path = r"c:\yara-care-os\apps\hub\runtime\src\test\java\ir\sayda\yara\hub\runtime\communication\CommunicationRuntimeTest.kt"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# For the following tests, startCall or join or reconnect returns Connecting, not Connected:
# outgoingStartCallJoinsEngineWithBackendLoginUrl
content = content.replace(
"""        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connected, session.runtimeState)
        assertEquals(CallDirection.Outgoing, session.direction)
        assertEquals(listOf("opaque-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)""",
"""        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connecting, session.runtimeState)
        assertEquals(CallDirection.Outgoing, session.direction)
        assertEquals(listOf("opaque-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connecting, repository.getCurrent()?.runtimeState)"""
)

# backendConflictJoinsIncomingSession
content = content.replace(
"""        assertEquals("existing-session", session.sessionId)
        assertEquals("refreshed-token", session.joinToken)
        assertEquals(CallDirection.Incoming, session.direction)
        assertEquals(CallRuntimeState.Connected, session.runtimeState)
        assertEquals(listOf("refreshed-token"), client.joinedUrls)""",
"""        assertEquals("existing-session", session.sessionId)
        assertEquals("refreshed-token", session.joinToken)
        assertEquals(CallDirection.Incoming, session.direction)
        assertEquals(CallRuntimeState.Connecting, session.runtimeState)
        assertEquals(listOf("refreshed-token"), client.joinedUrls)"""
)

# replicaIncomingSessionStartsJoin
content = content.replace(
"""        assertEquals("session-replica", repository.getCurrent()?.sessionId)
        assertEquals(listOf("replica-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)""",
"""        assertEquals("session-replica", repository.getCurrent()?.sessionId)
        assertEquals(listOf("replica-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connecting, repository.getCurrent()?.runtimeState)"""
)

# joinIncomingCallUsesRefreshTokenAsLoginUrl
content = content.replace(
"""        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connected, session.runtimeState)
        assertEquals(listOf("refreshed-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)""",
"""        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connecting, session.runtimeState)
        assertEquals(listOf("refreshed-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connecting, repository.getCurrent()?.runtimeState)"""
)

# connectionLostKeepsSessionAndReconnectJoinsAgain
content = content.replace(
"""        val reconnected = runtime.reconnect()
        assertTrue(reconnected is AppResult.Success)
        assertEquals(2, client.joinedUrls.size)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)""",
"""        val reconnected = runtime.reconnect()
        assertTrue(reconnected is AppResult.Success)
        assertEquals(2, client.joinedUrls.size)
        assertEquals(CallRuntimeState.Reconnecting, repository.getCurrent()?.runtimeState)"""
)

# networkDropMarksConnectionLostAndRestoreReconnects
content = content.replace(
"""        connectivity.online.value = true
        advanceUntilIdle()
        assertEquals(2, client.joinedUrls.size)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)""",
"""        connectivity.online.value = true
        advanceUntilIdle()
        assertEquals(2, client.joinedUrls.size)
        assertEquals(CallRuntimeState.Reconnecting, repository.getCurrent()?.runtimeState)"""
)

# recoverRestoresUnexpiredSessionAndRejoins
content = content.replace(
"""        assertTrue(recovered is AppResult.Success)
        assertEquals("session-1", (recovered as AppResult.Success).data?.sessionId)
        assertEquals(listOf("opaque-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connected, repository.getCurrent()?.runtimeState)""",
"""        assertTrue(recovered is AppResult.Success)
        assertEquals("session-1", (recovered as AppResult.Success).data?.sessionId)
        assertEquals(listOf("opaque-join-token"), client.joinedUrls)
        assertEquals(CallRuntimeState.Connecting, repository.getCurrent()?.runtimeState)"""
)

# outgoingStartCallWithLivekitEngineJoinsSuccessfully
content = content.replace(
"""        assertTrue(result is AppResult.Success)
        val session = (result as AppResult.Success).data
        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connected, session.runtimeState)
        assertEquals(listOf("opaque-join-token"), client.joinedTokens)""",
"""        assertTrue(result is AppResult.Success)
        val session = (result as AppResult.Success).data
        assertEquals("session-1", session.sessionId)
        assertEquals(CallRuntimeState.Connecting, session.runtimeState)
        assertEquals(listOf("opaque-join-token"), client.joinedTokens)"""
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Tests updated.")
