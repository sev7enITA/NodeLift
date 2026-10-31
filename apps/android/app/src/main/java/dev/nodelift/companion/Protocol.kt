package dev.nodelift.companion

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import org.json.JSONObject
import java.net.URL
import java.security.KeyStore
import java.security.MessageDigest
import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManagerFactory

data class Pairing(val url: String, val certificate: String, val sha256: String, val invite: String = "") {
    fun json(): JSONObject = JSONObject().put("url", url).put("certificate", certificate).put("sha256", sha256)
    companion object {
        fun parse(o: JSONObject): Pairing {
            val url = URL(o.getString("url"))
            require(url.protocol == "https" && url.userInfo == null && url.query == null && url.ref == null && (url.path.isEmpty() || url.path == "/")) { "Invito non valido: è richiesto HTTPS." }
            val parts = url.host.split('.').map { it.toIntOrNull() ?: -1 }
            require(parts.size == 4 && parts.all { it in 0..255 } && (parts[0] == 10 || parts[0] == 127 || parts[0] == 192 && parts[1] == 168 || parts[0] == 172 && parts[1] in 16..31)) { "Usa un computer nella rete locale." }
            val certificate = o.getString("certificate")
            require(certificate.length <= 16384)
            val cert = CertificateFactory.getInstance("X.509").generateCertificate(certificate.byteInputStream()) as X509Certificate
            cert.checkValidity()
            val hash = MessageDigest.getInstance("SHA-256").digest(cert.encoded).joinToString("") { "%02x".format(it) }
            require(hash == o.getString("sha256").lowercase()) { "Identità del computer non valida." }
            return Pairing(url.toString().trimEnd('/'), certificate, hash, o.optString("invite"))
        }
    }
}

class Client(val pairing: Pairing, var token: String = "") {
    @Volatile var lastConnectionId: String = ""
        private set
    private val factory = run {
        val store = KeyStore.getInstance(KeyStore.getDefaultType()).apply { load(null) }
        val cert = CertificateFactory.getInstance("X.509").generateCertificate(pairing.certificate.byteInputStream())
        store.setCertificateEntry("nodelift-host", cert)
        val tm = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm()).apply { init(store) }
        SSLContext.getInstance("TLS").apply { init(null, tm.trustManagers, null) }.socketFactory
    }
    @Volatile private var active: HttpsURLConnection? = null
    fun cancel() { active?.disconnect() }
    fun bytes(path: String, body: ByteArray? = null, raw: Boolean = false): ByteArray {
        val connection = URL(pairing.url + path).openConnection() as HttpsURLConnection
        active = connection
        var completed = false
        try {
            connection.sslSocketFactory = factory // Hostname verification remains enabled.
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 6000; connection.readTimeout = 10000
            connection.setRequestProperty("Accept-Encoding", "identity")
            if (token.isNotEmpty()) connection.setRequestProperty("Authorization", "Bearer $token")
            if (body != null) {
                connection.requestMethod = "POST"; connection.doOutput = true
                connection.setRequestProperty("Content-Type", if (raw) "application/octet-stream" else "application/json")
                connection.setFixedLengthStreamingMode(body.size)
                connection.outputStream.use { it.write(body) }
            }
            val status = connection.responseCode
            lastConnectionId = connection.getHeaderField("X-NodeLift-Connection-ID") ?: ""
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val data = stream?.use { it.readBytes() } ?: byteArrayOf()
            require(status in 200..299) { if (status == 401) "Associazione scaduta o revocata. Crea un nuovo invito." else "Il computer ha rifiutato la richiesta ($status)." }
            require(data.size <= 1048576) { "Risposta troppo grande." }
            completed = true
            return data
        } finally { active = null; if (!completed) connection.disconnect() }
    }
    fun json(path: String, body: JSONObject): JSONObject = JSONObject(String(bytes(path, body.toString().toByteArray()), Charsets.UTF_8))
}

object Vault {
    private const val ALIAS = "nodelift-session-v1"
    private fun key(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        if (ks.containsAlias(ALIAS)) return ks.getKey(ALIAS, null) as SecretKey
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    fun save(context: Context, value: JSONObject) {
        val c = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        val data = c.doFinal(value.toString().toByteArray())
        context.getSharedPreferences("vault", 0).edit().putString("iv", Base64.encodeToString(c.iv, Base64.NO_WRAP)).putString("data", Base64.encodeToString(data, Base64.NO_WRAP)).commit()
    }
    fun load(context: Context): JSONObject? = try {
        val prefs = context.getSharedPreferences("vault", 0)
        val encoded = prefs.getString("data", null)
        if (encoded == null) null else {
            val c = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(prefs.getString("iv", ""), Base64.NO_WRAP))) }
            JSONObject(String(c.doFinal(Base64.decode(encoded, Base64.NO_WRAP)), Charsets.UTF_8))
        }
    } catch (_: Exception) { null }
    fun clear(context: Context) { context.getSharedPreferences("vault", 0).edit().clear().commit() }
}
