package dev.nodelift.companion

import java.net.ConnectException
import java.net.NoRouteToHostException
import java.net.SocketTimeoutException
import javax.net.ssl.SSLException

/** Stable localizable feedback; never include private URLs or exception text in diagnostics. */
fun connectionFailureMessage(error: Throwable): String = when (error) {
    is SocketTimeoutException, is ConnectException, is NoRouteToHostException ->
        "Cannot reach your computer. Keep both devices on the same Wi-Fi or hotspot, then create a new QR code on the computer. Hotspot client isolation can also block the connection."
    is SSLException ->
        "The computer's secure identity could not be verified. Create a new QR code and confirm its identity before pairing again."
    else -> error.message ?: "Connection failed"
}
