package dev.nodelift.companion

import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/** Private app identity, scoped to a host. Never use model, IP, MAC or IMEI. */
object EnrollmentIdentity {
    private fun hmac(key: ByteArray, message: String): String = Mac.getInstance("HmacSHA256").run {
        init(SecretKeySpec(key, "HmacSHA256"))
        doFinal(message.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
    }
    fun scoped(root: ByteArray, scope: String): String = hmac(root, "nodelift-device-v1\n$scope")
    fun continuity(token: String, invite: String): String = hmac(
        MessageDigest.getInstance("SHA-256").digest(token.toByteArray(Charsets.UTF_8)), "nodelift-repair-v1\n$invite")
}
