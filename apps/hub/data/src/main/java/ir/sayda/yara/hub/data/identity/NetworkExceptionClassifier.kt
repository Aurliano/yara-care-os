package ir.sayda.yara.hub.data.identity

import kotlinx.coroutines.TimeoutCancellationException
import retrofit2.HttpException
import java.net.ConnectException
import java.net.NoRouteToHostException
import java.net.PortUnreachableException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

object NetworkExceptionClassifier {

    /**
     * Determines whether an exception is strictly a pure transport-layer connection failure.
     *
     * SECURITY RULE (Task 2.4 Condition 1):
     * - Any HTTP status code from the server (e.g. 401 Unauthorized, 403 Forbidden, 404 Not Found)
     *   indicates that network transport SUCCEEDED and the server issued an application-level
     *   rejection or revocation. This is NEVER classified as a pure transport failure.
     * - Only precisely known connection/socket exceptions (ConnectException, SocketTimeoutException,
     *   UnknownHostException, NoRouteToHostException, PortUnreachableException, TimeoutCancellationException)
     *   are considered pure transport failures.
     * - Any unknown, ambiguous, or SSL verification exception defaults to FALSE (fail-safe).
     */
    fun isPureTransportException(throwable: Throwable?): Boolean {
        var current: Throwable? = throwable
        while (current != null) {
            // Did we receive an HTTP response from the backend?
            if (current is HttpException) {
                return false
            }
            if (
                current is ConnectException ||
                current is SocketTimeoutException ||
                current is UnknownHostException ||
                current is NoRouteToHostException ||
                current is PortUnreachableException ||
                current is TimeoutCancellationException
            ) {
                return true
            }
            current = current.cause
        }
        return false
    }
}
