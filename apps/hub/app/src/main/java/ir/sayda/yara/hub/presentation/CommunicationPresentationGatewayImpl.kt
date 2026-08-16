package ir.sayda.yara.hub.presentation

import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CommunicationPresentationGatewayImpl @Inject constructor() : CommunicationPresentationGateway {

    private val sessions = MutableSharedFlow<CallSession>(replay = 1, extraBufferCapacity = 8)

    override suspend fun onCallSession(session: CallSession) {
        sessions.emit(session)
    }

    override fun observeCallSessions(): Flow<CallSession> = sessions.asSharedFlow()
}
