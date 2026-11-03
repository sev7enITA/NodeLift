package dev.nodelift.companion

import android.app.ActivityManager
import android.content.Context
import org.json.JSONObject
import org.json.JSONArray
import android.os.SystemClock
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
        check(handle != 0L) { "Engine unavailable" }
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
        check(model.exists()) { "Download the draft from your computer first" }
        val size=model.length()
        check(size in 1..(1024L*1024*1024)) { "Model exceeds the mobile limit of 1 GiB" }
        val mem=ActivityManager.MemoryInfo().also { context.getSystemService(ActivityManager::class.java).getMemoryInfo(it) }
        check(mem.availMem > size*2+268435456L && !mem.lowMemory) { "Not enough memory: free RAM before loading the model" }
        val digest=MessageDigest.getInstance("SHA-256")
        model.inputStream().use { input -> val b=ByteArray(262144);while(true){val n=input.read(b);if(n<0)break;digest.update(b,0,n)} }
        sha256=digest.digest().joinToString(""){"%02x".format(it)}
        check(sha256 == prefs.getString("sha256",null)) { "Model hash mismatch: download the draft again" }
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
        check(bytes in 1..(1024L*1024*1024)) { "Choose a draft no larger than 1 GiB for this build" }
        check(context.filesDir.usableSpace > bytes+536870912L) { "Not enough free storage" }
        val sha=offer.getString("sha256");check(sha.matches(Regex("[0-9a-f]{64}")))
        client.downloadModel(model,bytes,sha,progress)
        prefs.edit().putString("sha256",sha).putString("name",offer.getString("name")).apply()
        loadSaved()
    }
    private data class Prepared(val parent: String, val epoch: String, val sequence: Int,
        val base: List<Int>, val tokens: List<Int>, val timing: JSONObject, val completed: Long)
    private var prepared: Prepared? = null
    private fun ids(array: JSONArray) = (0 until array.length()).map { array.getInt(it) }
    private fun now() = SystemClock.elapsedRealtimeNanos()
    private fun elapsed(start: Long) = (now()-start)/1e6
    private fun collectPrior(t: JSONObject, p: Prepared, used: LookaheadPolicy.Reuse) {
        t.put("lookahead_parent_id",p.parent).put("lookahead_computed",p.tokens.size)
            .put("lookahead_reused",used.tokens.size).put("lookahead_prefix_consumed",used.consumed)
            .put("lookahead_discarded",used.discarded)
            .put("lookahead_prior_native_ms",p.timing.optDouble("native_total_ms",0.0))
            .put("lookahead_prior_sync_ms",p.timing.optDouble("native_sync_ms",0.0))
            .put("lookahead_prior_after_sync_ms",p.timing.optDouble("native_after_sync_ms",0.0))
    }
    fun draft(work: JSONObject): JSONObject {
        val started=now();val answer=JSONObject();val timing=JSONObject().put("schema_version",1)
        try {
            for(key in listOf("id","epoch","prefix_hash","tokenizer_fingerprint","model_sha256")) answer.put(key,work.get(key))
            if(work.has("sequence")) answer.put("sequence",work.getInt("sequence"))
            check(work.getString("model_sha256")==sha256 && work.getString("tokenizer_fingerprint")==fingerprint) { "Model or tokenizer mismatch" }
            val op=work.getString("op");check(op=="draft" || op=="finish")
            val prefix=work.getJSONArray("prefix");check(prefix.length() in 1..loadedContext)
            val digest=MessageDigest.getInstance("SHA-256").digest(prefix.toString().toByteArray()).joinToString(""){"%02x".format(it)}
            check(digest==work.getString("prefix_hash")) { "Invalid context" }
            val count=work.getInt("count")
            check(if(op=="finish") count==0 else count in 1..16 && prefix.length()+count<=loadedContext) { "Mobile context capacity exceeded" }
            val prior=prepared;prepared=null
            var tokens=emptyList<Int>()
            if(prior!=null && prior.epoch==work.getString("epoch")) {
                val use=if(op=="finish") LookaheadPolicy.Reuse(emptyList(),0,prior.tokens.size)
                    else LookaheadPolicy.select(prior.base,prior.tokens,ids(prefix),count,
                        work.optString("pipeline")=="bounded_v1" && prior.sequence==work.getInt("sequence"),
                        now()-prior.completed>2_000_000_000L)
                collectPrior(timing,prior,use);tokens=use.tokens
            }
            timing.put("worker_validation_ms",elapsed(started))
            if(op=="draft" && tokens.isEmpty()) {
                val nativeStart=now()
                val result=native?.call("draft",JSONObject().put("prefix",prefix).put("count",count)) ?: error("Draft not loaded")
                timing.put("worker_native_ms",elapsed(nativeStart))
                result.optJSONObject("timing")?.let { nativeTiming ->
                    for(key in nativeTiming.keys()) if(key!="schema_version") timing.put(key,nativeTiming.get(key))
                }
                tokens=ids(result.getJSONArray("tokens"))
                answer.put("eos",result.optBoolean("eos"))
            }
            answer.put("tokens",JSONArray(tokens))
            if(op=="draft") NodeService.lastResult=ui("Draft: {0} proposed tokens · {1} ms",tokens.size,"%.1f".format(elapsed(started)))
        } catch(e:Exception) { prepared=null;answer.put("error",e.message ?: "Draft generation failed") }
        timing.put("worker_total_ms",elapsed(started));answer.put("telemetry",timing)
        return answer
    }
    // Runs only after the host acknowledges the current result. The service has
    // one inference thread, so at most one bounded block exists at any time.
    fun prepareLookahead(work: JSONObject, answer: JSONObject) {
        if(work.optString("pipeline")!="bounded_v1" || work.optString("op")!="draft" ||
            answer.has("error") || answer.optBoolean("eos")) return
        val proposal=answer.optJSONArray("tokens") ?: return
        val remaining=work.optInt("remaining",0)-proposal.length()
        if(proposal.length()==0 || remaining<=1) return
        val base=ids(work.getJSONArray("prefix"))+ids(proposal)
        val count=minOf(work.getInt("count")+1,remaining,loadedContext-base.size)
        if(count<=0) return
        try {
            val result=native?.call("draft",JSONObject().put("prefix",JSONArray(base)).put("count",count)) ?: return
            prepared=Prepared(work.getString("id"),work.getString("epoch"),work.getInt("sequence")+1,
                base,ids(result.getJSONArray("tokens")),result.optJSONObject("timing") ?: JSONObject(),now())
        } catch(e:Exception) { prepared=null } // A failed prediction never becomes output.
    }
    fun cancel(){native?.cancel()}
    override fun close(){prepared=null;native?.close();native=null}
}
