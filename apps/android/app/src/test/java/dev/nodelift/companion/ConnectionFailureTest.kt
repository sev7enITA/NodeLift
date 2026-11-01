package dev.nodelift.companion

import org.junit.Assert.*
import org.junit.Test
import java.net.SocketTimeoutException
import javax.net.ssl.SSLHandshakeException

class ConnectionFailureTest {
    @Test fun timeoutGivesNetworkGuidanceWithoutPrivateExceptionText() {
        val message = connectionFailureMessage(SocketTimeoutException("private-host-and-token"))
        assertTrue(message.contains("same Wi-Fi"))
        assertFalse(message.contains("private-host-and-token"))
    }
    @Test fun tlsFailureNeverSuggestsDisablingVerification() {
        val message = connectionFailureMessage(SSLHandshakeException("pin mismatch"))
        assertTrue(message.contains("secure identity"))
        assertTrue(message.contains("confirm"))
        assertFalse(message.contains("pin mismatch"))
    }
    @Test fun expiredInvitationKeepsExistingActionableFeedback() {
        val message = "Pairing expired or revoked. Create a new invitation."
        assertEquals(message, connectionFailureMessage(IllegalArgumentException(message)))
    }
}
