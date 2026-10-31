package dev.nodelift.companion

import android.app.ActivityManager
import android.content.Context
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest

class NativeEngine : AutoCloseable {
    companion object { init { System.loadLibrary("nodelift") } }
    private external fun create(): Long
    private external fun request(handle: Long, value: String): String
    private external fun interrupt(handle: Long)
    private external fun dispose(handle: Long)
    @Volatile private var handle = create()
    @Synchronized fun call(op: String, args: JSONObject = JSONObject()): JSONObject {
        check(handle != 0L) { "Motore non disponibile" }
        val response = JSONObject(request(handle, args.put("op",op).toString()))
        if(response.has("error")) error(response.getString("error"))
        return response
    }
    fun cancel() { if(handle != 0L) interrupt(handle) }
    @Synchronized override fun close() { if(handle != 0L) { dispose(handle); handle=0L } }
}

class MobileDraft(private val context: Context) : AutoCloseable {
    @Volatile private var native: NativeEngine? = null
    private var loadedContext = 2048
    var sha256 = ""; private set
    var fingerprint = ""; private set
    val ready get() = native != null
    private val prefs get() = context.getSharedPreferences("engine",0)
    private val model get() = File(context.filesDir,"draft.gguf")

    fun loadSaved() {
        check(model.exists()) { "Scarica prima il draft dal computer" }
        val size=model.length()
        check(size in 1..(1024L*1024*1024)) { "Modello oltre il limite mobile di 1 GiB" }
        val mem=ActivityManager.MemoryInfo().also { context.getSystemService(ActivityManager::class.java).getMemoryInfo(it) }
        check(mem.availMem > size*2+268435456L && !mem.lowMemory) { "Memoria insufficiente: libera RAM prima di caricare il modello" }
        val digest=MessageDigest.getInstance("SHA-256")
        model.inputStream().use { input -> val b=ByteArray(262144);while(true){val n=input.read(b);if(n<0)break;digest.update(b,0,n)} }
        sha256=digest.digest().joinToString(""){"%02x".format(it)}
        check(sha256 == prefs.getString("sha256",null)) { "Hash del modello non valido: riscarica il draft" }
        native?.close();native=null
        val created=NativeEngine()
        try {
            val result=created.call("load",JSONObject().put("path",model.absolutePath)
                .put("threads",prefs.getInt("threads",4).coerceIn(1,8))
                .put("n_ctx",prefs.getInt("n_ctx",2048).coerceIn(512,4096)).put("gpu_layers",0))
            loadedContext=result.getInt("n_ctx");fingerprint=result.getString("tokenizer_fingerprint");native=created
        } catch(e:Exception){created.close();throw e}
    }
    fun download(client: Client, progress: (Long,Long)->Unit) {
        val offer=JSONObject(String(client.bytes("/v1/engine/model-info"),Charsets.UTF_8))
        val bytes=offer.getLong("bytes")
        check(bytes in 1..(1024L*1024*1024)) { "Per questa build scegli un draft entro 1 GiB" }
        check(context.filesDir.usableSpace > bytes+536870912L) { "Spazio libero insufficiente" }
        val sha=offer.getString("sha256");check(sha.matches(Regex("[0-9a-f]{64}")))
        client.downloadModel(model,bytes,sha,progress)
        prefs.edit().putString("sha256",sha).putString("name",offer.getString("name")).apply()
        loadSaved()
    }
    fun draft(work: JSONObject): JSONObject {
        val answer=JSONObject()
        try {
            for(key in listOf("id","epoch","prefix_hash","tokenizer_fingerprint","model_sha256")) answer.put(key,work.get(key))
            check(work.getString("op")=="draft")
            check(work.getString("model_sha256")==sha256 && work.getString("tokenizer_fingerprint")==fingerprint) { "Modello o tokenizer non corrispondente" }
            val prefix=work.getJSONArray("prefix");check(prefix.length() in 1 until loadedContext)
            val digest=MessageDigest.getInstance("SHA-256").digest(prefix.toString().toByteArray()).joinToString(""){"%02x".format(it)}
            check(digest==work.getString("prefix_hash")) { "Contesto non valido" }
            val count=work.getInt("count");check(count in 1..16 && prefix.length()+count<=loadedContext) { "Contesto mobile insufficiente" }
            val result=native?.call("draft",JSONObject().put("prefix",prefix).put("count",count)) ?: error("Draft non caricato")
            answer.put("tokens",result.getJSONArray("tokens"))
            NodeService.lastResult="Draft: ${result.getJSONArray("tokens").length()} token proposti · %.1f ms".format(result.getDouble("ms"))
        } catch(e:Exception) { answer.put("error",e.message ?: "Draft fallito") }
        return answer
    }
    fun cancel(){native?.cancel()}
    override fun close(){native?.close();native=null}
}
