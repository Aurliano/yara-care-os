package ir.sayda.yara.hub.data.communication

import ir.sayda.yara.hub.core.communication.CommunicationRepository
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CommunicationRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : CommunicationRepository {
    private val dao = database.localCallSessionDao()

    override suspend fun saveCurrent(session: CallSession) {
        dao.upsert(session.toEntity())
    }

    override suspend fun getCurrent(): CallSession? = dao.getCurrent()?.toDomain()

    override suspend fun clear() {
        dao.deleteAll()
    }

    override fun observeCurrent(): Flow<CallSession?> =
        dao.observeCurrent().map { entity -> entity?.toDomain() }
}
