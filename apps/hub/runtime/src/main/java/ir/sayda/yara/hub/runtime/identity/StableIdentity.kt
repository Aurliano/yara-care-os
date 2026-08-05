package ir.sayda.yara.hub.runtime.identity

import java.nio.ByteBuffer
import java.security.MessageDigest
import java.util.UUID

private val SCHEDULING_NAMESPACE = UUID.fromString("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
private val WORKFLOW_NAMESPACE = UUID.fromString("a3f8e7d1-2b4c-5a6e-8f90-1a2b3c4d5e6f")

fun computeOccurrenceId(scheduleDefinitionId: String, originalTimeIsoUtc: String): String {
    return uuid5(SCHEDULING_NAMESPACE, "$scheduleDefinitionId:$originalTimeIsoUtc").toString()
}

fun computeExecutionId(occurrenceId: String): String {
    return uuid5(WORKFLOW_NAMESPACE, "execution:$occurrenceId").toString()
}

fun uuid5(namespace: UUID, name: String): UUID {
    val md = MessageDigest.getInstance("SHA-1")
    md.update(toBytes(namespace))
    md.update(name.toByteArray(Charsets.UTF_8))
    val hash = md.digest().copyOf(16)
    hash[6] = ((hash[6].toInt() and 0x0f) or 0x50).toByte()
    hash[8] = ((hash[8].toInt() and 0x3f) or 0x80).toByte()
    val buffer = ByteBuffer.wrap(hash)
    return UUID(buffer.long, buffer.long)
}

private fun toBytes(uuid: UUID): ByteArray {
    val buffer = ByteBuffer.allocate(16)
    buffer.putLong(uuid.mostSignificantBits)
    buffer.putLong(uuid.leastSignificantBits)
    return buffer.array()
}
