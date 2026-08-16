package ir.sayda.yara.hub.core.communication

class ActiveCallExistsException(
    message: String = "An active communication session already exists.",
) : IllegalStateException(message)
