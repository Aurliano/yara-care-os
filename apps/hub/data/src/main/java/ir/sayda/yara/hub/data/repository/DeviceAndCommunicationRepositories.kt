package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.core.domain.model.CommunicationSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.Device
import ir.sayda.yara.hub.core.domain.model.DeviceCommand
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.DeviceReplicaRepository
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeviceReplicaRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : DeviceReplicaRepository {
    private val deviceDao = database.deviceDao()
    private val commandDao = database.deviceCommandDao()

    override suspend fun upsertDevice(device: Device) {
        deviceDao.upsert(device.toEntity())
    }

    override suspend fun upsertCommand(command: DeviceCommand) {
        commandDao.upsert(command.toEntity())
    }

    override suspend fun getQueuedCommands(): List<DeviceCommand> =
        commandDao.getQueued().map { it.toDomain() }
}

@Singleton
class CommunicationReplicaRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : CommunicationReplicaRepository {
    private val contactDao = database.contactDao()
    private val sessionDao = database.communicationSessionDao()

    override fun observePriorityContacts(elderId: String): Flow<List<Contact>> =
        contactDao.observePriorityByElder(elderId).map { list -> list.map { it.toDomain() } }

    override suspend fun upsertContact(contact: Contact) {
        contactDao.upsert(contact.toEntity())
    }

    override suspend fun upsertSession(session: CommunicationSession) {
        sessionDao.upsert(session.toEntity())
    }
}
