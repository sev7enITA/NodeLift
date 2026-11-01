package dev.nodelift.companion

import android.app.Activity
import android.app.Instrumentation
import android.os.Bundle
import org.json.JSONObject

/** Integration test on a disposable emulator; never a performance benchmark. */
class ProtocolCheck : Instrumentation() {
    override fun onCreate(arguments: Bundle?) { super.onCreate(arguments); start() }
    override fun onStart() {
        Thread {
            val result = Bundle()
            try {
                val ticket = context.assets.open("pairing.json").bufferedReader().use { JSONObject(it.readText()) }
                val pairing = Pairing.parse(ticket)
                val client = Client(pairing)
                val reply = client.json("/v1/pair",JSONObject().put("invite",pairing.invite).put("name","Android emulator protocol QA").put("capabilities",JSONObject().put("model","EMULATOR: NOT A PHONE").put("os","Android test")))
                client.token = reply.getString("token")
                check(client.bytes("/v1/probe?size=16384").size == 16384)
                val uploaded = JSONObject(String(client.bytes("/v1/upload", ByteArray(16384), true)))
                check(uploaded.getInt("bytes") == 16384)
                client.json("/v1/heartbeat",JSONObject().put("model","EMULATOR: NOT A PHONE"))
                val damaged = pairing.json().put("sha256","0".repeat(64))
                var rejected = false
                try { Pairing.parse(damaged) } catch (_:Exception) { rejected = true }
                check(rejected)
                // Use a distinct vault context for QA and remove it after checking round trip.
                Vault.save(context,JSONObject().put("qa","roundtrip"))
                check(Vault.load(context)?.getString("qa") == "roundtrip")
                Vault.clear(context)
                check(Vault.load(context) == null)
                result.putString("stream","PASS: Android TLS enrollment, authenticated upload/download, heartbeat, invalid fingerprint rejection, Keystore round trip. Emulator only.\n")
                finish(Activity.RESULT_OK,result)
            } catch (error:Exception) {
                result.putString("stream","FAIL: ${error.javaClass.simpleName}: ${error.message}\n")
                finish(Activity.RESULT_CANCELED,result)
            }
        }.start()
    }
}
