package dev.nodelift.companion

import android.util.Base64
import org.json.JSONObject
import java.security.MessageDigest

/** Versioned offline QR; reconstructs the existing invitation before its TLS validation. */
object PairingCode {
    private const val PREFIX = "nodelift://pair/v1/"
    fun decode(value: String, now: Double = System.currentTimeMillis()/1000.0): JSONObject {
        require(value.length <= 8192) { "Invalid invitation" }
        val text = value.trim()
        val version=if(text.startsWith("nodelift://pair/v2/"))2 else 1
        val prefix=if(version==2)"nodelift://pair/v2/" else PREFIX
        val result = if (text.startsWith(prefix)) {
            val parts=text.removePrefix(prefix).split('/')
            require(parts.size==(if(version==2)5 else 4) && parts[0].matches(Regex("[0-9.]+:[0-9]{1,5}")) && parts[1].matches(Regex("[0-9]{10}")) && parts[2].matches(Regex("[A-Za-z0-9_-]{32}")) && parts.last().matches(Regex("[A-Za-z0-9_-]{64,6000}"))) { "Invalid invitation" }
            val der=Base64.decode(parts.last(),Base64.URL_SAFE or Base64.NO_WRAP)
            val pem="-----BEGIN CERTIFICATE-----\n"+Base64.encodeToString(der,Base64.NO_WRAP).chunked(64).joinToString("\n")+"\n-----END CERTIFICATE-----\n"
            JSONObject().put("protocol",version).apply {if(version==2)put("tls_name",parts[3])}.put("url","https://"+parts[0]).put("certificate",pem)
                .put("sha256",MessageDigest.getInstance("SHA-256").digest(der).joinToString(""){"%02x".format(it)})
                .put("invite",parts[2]).put("expires_at",parts[1].toLong())
        } else JSONObject(text)
        require(result.getInt("protocol") in 1..2 && result.getString("invite").matches(Regex("[A-Za-z0-9_-]{32}"))) { "Invalid invitation" }
        require(result.getDouble("expires_at").isFinite() && result.getDouble("expires_at")>now) { "Invitation expired. Create a new one." }
        val parsed=Pairing.parse(result)
        val port=java.net.URL(parsed.url).port
        require(port==-1 || port in 1..65535) { "Invalid invitation" }
        return result
    }
}
