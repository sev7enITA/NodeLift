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
import javax.net.ssl.X509TrustManager
import java.security.cert.CertificateException
import java.io.File
import java.io.ByteArrayOutputStream
import java.nio.file.Files
import java.nio.file.StandardCopyOption

data class Pairing(val url: String, val certificate: String, val sha256: String, val invite: String = "", val protocol: Int = 1, val tlsName: String? = null) {
    fun json(): JSONObject = JSONObject().put("url", url).put("certificate", certificate).put("sha256", sha256).put("protocol", protocol).put("tls_name", tlsName)
    companion object {
        fun parse(o: JSONObject): Pairing {
            val protocol = o.optInt("protocol",1)
            require(protocol in 1..2) { "Unsupported pairing protocol" }
            val tlsName = if(protocol==2) o.getString("tls_name") else null
            require(tlsName==null || tlsName.matches(Regex("nodelift-[0-9a-f]{32}\\.local"))) { "Invalid computer identity." }
            val url = URL(o.getString("url"))
            require(url.protocol == "https" && url.userInfo == null && url.query == null && url.ref == null && (url.path.isEmpty() || url.path == "/")) { "Invalid invitation: HTTPS is required." }
            require(url.port == -1 || url.port in 1..65535) { "Invalid port" }
            val parts = url.host.split('.').map { it.toIntOrNull() ?: -1 }
            require(parts.size == 4 && parts.all { it in 0..255 } && (parts[0] == 10 || parts[0] == 127 || parts[0] == 192 && parts[1] == 168 || parts[0] == 172 && parts[1] in 16..31)) { "Use a computer on your local network." }
            val certificate = o.getString("certificate")
            require(certificate.length <= 16384)
            val cert = CertificateFactory.getInstance("X.509").generateCertificate(certificate.byteInputStream()) as X509Certificate
            cert.checkValidity()
            val hash = MessageDigest.getInstance("SHA-256").digest(cert.encoded).joinToString("") { "%02x".format(it) }
            require(hash == o.getString("sha256").lowercase()) { "Invalid computer identity." }
            return Pairing(url.toString().trimEnd('/'), certificate, hash, o.optString("invite"), protocol, tlsName)
        }
    }
}

class DiscardedDraft : Exception("Draft lease expired; result discarded")

class Client(val pairing: Pairing, var token: String = "", private val context: Context? = null, private val onAuthenticatedResponse: (() -> Unit)? = null) {
    @Volatile var lastConnectionId: String = ""
        private set
    private val factory = run {
        val store = KeyStore.getInstance(KeyStore.getDefaultType()).apply { load(null) }
        val cert = CertificateFactory.getInstance("X.509").generateCertificate(pairing.certificate.byteInputStream())
        store.setCertificateEntry("nodelift-host", cert)
        val tm = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm()).apply { init(store) }
        val delegate = tm.trustManagers.filterIsInstance<X509TrustManager>().single()
        val pinned = object : X509TrustManager {
            override fun getAcceptedIssuers(): Array<X509Certificate> = delegate.acceptedIssuers
            override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) = delegate.checkClientTrusted(chain, authType)
            override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {
                val leaf = chain.firstOrNull() ?: throw CertificateException("Missing server certificate")
                val fingerprint = MessageDigest.getInstance("SHA-256").digest(leaf.encoded).joinToString("") { "%02x".format(it) }
                if (fingerprint != pairing.sha256) throw CertificateException("Computer identity changed")
                delegate.checkServerTrusted(chain, authType)
            }
        }
        SSLContext.getInstance("TLS").apply { init(null, arrayOf(pinned), null) }.socketFactory
    }
    private fun verifyRoamingName(expected:String,session:javax.net.ssl.SSLSession):Boolean = try {
        val leaf=session.peerCertificates.first() as X509Certificate
        leaf.checkValidity()
        val names=leaf.subjectAlternativeNames.orEmpty().filter {it.size>=2 && it[0]==2}.mapNotNull {it[1] as? String}
        RoamingIdentity.matchesName(expected,names) && MessageDigest.getInstance("SHA-256").digest(leaf.encoded).joinToString(""){"%02x".format(it)}==pairing.sha256
    } catch(_:Exception) {false}
    private fun openLocalConnection(url: URL): HttpsURLConnection {
        val cm = context?.getSystemService(android.net.ConnectivityManager::class.java)
        val destination = java.net.InetAddress.getByName(url.host) // Validated literal IPv4; no DNS lookup.
        // A Wi-Fi network may have no Internet validation while cellular remains default.
        // Bind this request only when that LAN has a specific route to the paired host.
        // Tethering is not always exposed as a Network: retain OS routing in that case.
        @Suppress("DEPRECATION")
        val local = cm?.allNetworks?.firstOrNull { network ->
            val caps = cm.getNetworkCapabilities(network)
            val lan = caps?.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) == true ||
                caps?.hasTransport(android.net.NetworkCapabilities.TRANSPORT_ETHERNET) == true
            lan && cm.getLinkProperties(network)?.routes?.any { !it.isDefaultRoute && it.matches(destination) } == true
        }
        val route = if (local != null) {
            if (cm?.getNetworkCapabilities(local)?.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) == true) "wifi" else "ethernet"
        } else "system"
        if (route != lastRoute) {
            Diagnostics.record(when (route) {
                "wifi" -> DiagnosticEvent.ROUTE_WIFI
                "ethernet" -> DiagnosticEvent.ROUTE_ETHERNET
                else -> DiagnosticEvent.ROUTE_SYSTEM
            })
            lastRoute = route
        }
        return (local?.openConnection(url) ?: url.openConnection()) as HttpsURLConnection
    }
    @Volatile var lastRoute: String = "unknown"
        private set
    @Volatile private var active: HttpsURLConnection? = null
    fun cancel() { active?.disconnect() }
    fun bytes(path: String, body: ByteArray? = null, raw: Boolean = false): ByteArray {
        val connection = openLocalConnection(URL(pairing.url + path))
        active = connection
        var completed = false
        try {
            connection.sslSocketFactory = factory
            pairing.tlsName?.let { expected -> connection.hostnameVerifier = javax.net.ssl.HostnameVerifier { _, session -> verifyRoamingName(expected,session) } }
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
            val data = stream?.use { input ->
                val output=ByteArrayOutputStream();val buffer=ByteArray(16384)
                while(true){val count=input.read(buffer);if(count<0)break;require(output.size()+count<=1048576){"Response too large."};output.write(buffer,0,count)}
                output.toByteArray()
            } ?: byteArrayOf()
            if(path=="/v1/engine/result" && status==400 &&
                runCatching { JSONObject(String(data,Charsets.UTF_8)).optString("error") }.getOrNull()=="unknown, expired or replayed inference lease") {
                completed=true
                if(token.isNotEmpty())onAuthenticatedResponse?.invoke()
                throw DiscardedDraft()
            }
            require(status in 200..299) { if (status == 401) "Pairing expired or revoked. Create a new invitation." else "The computer rejected the request ($status)." }
            require(data.size <= 1048576) { "Response too large." }
            if(token.isNotEmpty())onAuthenticatedResponse?.invoke()
            completed = true
            return data
        } finally { active = null; if (!completed) connection.disconnect() }
    }
    fun json(path: String, body: JSONObject): JSONObject = JSONObject(String(bytes(path, body.toString().toByteArray()), Charsets.UTF_8))
    fun downloadModel(destination: File, expected: Long, sha256: String, progress: (Long,Long)->Unit) {
        val connection=openLocalConnection(URL(pairing.url+"/v1/engine/model"))
        active=connection
        val temporary=File(destination.parentFile,"draft.partial")
        try {
            connection.sslSocketFactory=factory
            pairing.tlsName?.let { expected -> connection.hostnameVerifier = javax.net.ssl.HostnameVerifier { _, session -> verifyRoamingName(expected,session) } }
            connection.instanceFollowRedirects=false
            connection.connectTimeout=6000;connection.readTimeout=15000
            connection.setRequestProperty("Authorization","Bearer $token")
            connection.setRequestProperty("Accept-Encoding","identity")
            check(connection.responseCode==200 && connection.contentLengthLong==expected) { "Model download unavailable" }
            var total=0L;val digest=MessageDigest.getInstance("SHA-256")
            connection.inputStream.use { input -> temporary.outputStream().use { output ->
                val buffer=ByteArray(262144)
                while(true){if(Thread.currentThread().isInterrupted)error("Download interrupted");val n=input.read(buffer);if(n<0)break;total+=n;check(total<=expected);digest.update(buffer,0,n);output.write(buffer,0,n);progress(total,expected)}
            } }
            check(total==expected && digest.digest().joinToString(""){"%02x".format(it)}==sha256) { "Model integrity check failed" }
            Files.move(temporary.toPath(),destination.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE)
        } finally { active=null;connection.disconnect();temporary.delete() }
    }
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
        check(context.getSharedPreferences("vault", 0).edit().putString("iv", Base64.encodeToString(c.iv, Base64.NO_WRAP)).putString("data", Base64.encodeToString(data, Base64.NO_WRAP)).commit()) { "Secure storage failed" }
    }
    fun load(context: Context): JSONObject? = try {
        val prefs = context.getSharedPreferences("vault", 0)
        val encoded = prefs.getString("data", null)
        if (encoded == null) null else {
            val c = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(prefs.getString("iv", ""), Base64.NO_WRAP))) }
            JSONObject(String(c.doFinal(Base64.decode(encoded, Base64.NO_WRAP)), Charsets.UTF_8))
        }
    } catch (_: Exception) { null }
    @Synchronized
    private fun identity(context: Context): ByteArray {
        val prefs = context.getSharedPreferences("vault_identity", 0)
        val encoded = prefs.getString("data", null)
        if (encoded != null) {
            val c = Cipher.getInstance("AES/GCM/NoPadding").apply {
                init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(prefs.getString("iv", ""), Base64.NO_WRAP)))
            }
            return c.doFinal(Base64.decode(encoded, Base64.NO_WRAP)).also { check(it.size == 32) }
        }
        val identity = ByteArray(32).also { java.security.SecureRandom().nextBytes(it) }
        val c = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        check(prefs.edit().putString("iv", Base64.encodeToString(c.iv, Base64.NO_WRAP))
            .putString("data", Base64.encodeToString(c.doFinal(identity), Base64.NO_WRAP)).commit()) { "Secure storage failed" }
        return identity
    }
    fun enrollment(context: Context, scope: String, invite: String, previous: JSONObject?): JSONObject {
        require(scope.matches(Regex("[0-9a-f]{64}"))) { "Update NodeLift on your computer before pairing." }
        val result = JSONObject().put("device_key", EnrollmentIdentity.scoped(identity(context), scope))
        if (previous != null) result.put("previous", JSONObject().put("node_id", previous.getString("node_id"))
            .put("proof", EnrollmentIdentity.continuity(previous.getString("token"), invite)))
        return result
    }
    fun clear(context: Context) { context.getSharedPreferences("vault", 0).edit().clear().commit() }
}
