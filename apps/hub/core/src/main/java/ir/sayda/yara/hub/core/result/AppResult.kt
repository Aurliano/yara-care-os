package ir.sayda.yara.hub.core.result

sealed class AppResult<out T> {
    data class Success<T>(val data: T) : AppResult<T>()
    data class Error(val exception: Throwable, val message: String = exception.message.orEmpty()) : AppResult<Nothing>()
}

inline fun <T> AppResult<T>.getOrNull(): T? = when (this) {
    is AppResult.Success -> data
    is AppResult.Error -> null
}

inline fun <T> AppResult<T>.getOrThrow(): T = when (this) {
    is AppResult.Success -> data
    is AppResult.Error -> throw exception
}
