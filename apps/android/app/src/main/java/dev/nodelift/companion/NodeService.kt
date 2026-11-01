package dev.nodelift.companion

import android.app.*
import android.content.*
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.*
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import kotlin.math.abs

class NodeService : Service() {
    companion object {

        private fun notification(context: Context): Notification {
            val manager = context.getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(NotificationChannel("session", L10n.text(context,"NodeLift session"), NotificationManager.IMPORTANCE_LOW))
            val open = PendingIntent.getActivity(context,0,Intent(context,MainActivity::class.java),PendingIntent.FLAG_IMMUTABLE)
            return Notification.Builder(context,"session").setSmallIcon(R.drawable.ic_node_mark)
                .setContentTitle(L10n.text(context,"NodeLift · active node"))
                .setContentText(L10n.text(context,"Measurements authorized by your computer. Open to pause."))
                .setContentIntent(open).setOngoing(true).build()
        }
        fun refreshNotification(context: Context) {
            if (running) context.getSystemService(NotificationManager::class.java).notify(1,notification(context))
        }
        @Volatile var running = false
        @Volatile var connected = false
        @Volatile var modelLoading = false
        @Volatile var engineReady = false
        @Volatile var status = ui("Ready to pair")
        @Volatile var lastResult = ui("No measurements yet")
        @Volatile var telemetry = ui("")
        val generation = AtomicLong(0)
        val downloadRequested = AtomicBoolean(false)
        @Volatile var engineStatus = ui("Draft not loaded · ARM64 CPU")
    }
    private val stop = AtomicBoolean(false)
    private var worker: Thread? = null
    private var client: Client? = null
    private var runId = 0L
    @Volatile private var mobileDraft: MobileDraft? = null
    private var thermalListener: PowerManager.OnThermalStatusChangedListener? = null
    private val enginePrefs get() = getSharedPreferences("engine",0)
    private fun energyAllowed(): Boolean {
        val battery=registerReceiver(null,IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val percent=battery?.getIntExtra(BatteryManager.EXTRA_LEVEL,-1) ?: -1
        return percent >= enginePrefs.getInt("min_battery",20) &&
            (Build.VERSION.SDK_INT<29 || getSystemService(PowerManager::class.java).currentThermalStatus<PowerManager.THERMAL_STATUS_MODERATE)
    }
    override fun onCreate() {
        super.onCreate()
        if(Build.VERSION.SDK_INT>=29) {
            thermalListener=PowerManager.OnThermalStatusChangedListener { level ->
                if(level>=PowerManager.THERMAL_STATUS_MODERATE) {mobileDraft?.cancel();engineStatus=ui("Thermal pause · waiting to cool down")}
            }
            getSystemService(PowerManager::class.java).addThermalStatusListener(mainExecutor,thermalListener!!)
        }
    }
    override fun onBind(intent: Intent?) = null
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (running) return START_NOT_STICKY
        Diagnostics.record(DiagnosticEvent.SESSION_START)
        startForeground(1, notification(this))
        stop.set(false); connected=false;running = true; runId = generation.incrementAndGet()
        val ticketText = intent?.getStringExtra("ticket")
        worker = Thread {
            try {
                status = ui("Connecting to your computer…")
                val saved = if (ticketText == null) Vault.load(this) else null
                val ticket = Pairing.parse(if (ticketText != null) JSONObject(ticketText) else saved?.getJSONObject("pairing") ?: error("Paste an invitation from your computer."))
                val c = Client(ticket, saved?.optString("token") ?: "", this); client = c
                if (ticketText != null) {
                    val response = c.json("/v1/pair", JSONObject().put("invite", ticket.invite).put("name", "${Build.MANUFACTURER} ${Build.MODEL}").put("capabilities", capabilities()))
                    c.token = response.getString("token")
                    Vault.save(this, JSONObject().put("pairing", ticket.json()).put("token", c.token).put("node_id", response.getString("node_id")))
                }
                var errors = 0
                var lastHeartbeat = 0L
                while (!stop.get()) {
                    try {
                        if(!enginePrefs.getBoolean("enabled",false) && mobileDraft!=null){mobileDraft?.close();mobileDraft=null;engineStatus=ui("Engine paused")}
                        if(downloadRequested.getAndSet(false)) {
                            Diagnostics.record(DiagnosticEvent.MODEL_LOADING)
                            modelLoading=true;engineReady=false
                            try {
                                check(energyAllowed()){ "Battery or thermal status prevents loading" }
                                mobileDraft?.close();mobileDraft=MobileDraft(this)
                                engineStatus=ui("Downloading draft from your computer…")
                                mobileDraft!!.download(c){done,total -> engineStatus=ui("Draft download: {0}%",done*100/total)}
                                enginePrefs.edit().putBoolean("enabled",true).apply()
                                engineStatus=ui("Draft ready · ARM64 CPU · SHA-256 verified");Diagnostics.record(DiagnosticEvent.MODEL_READY)
                            } catch(e:Exception){Diagnostics.record(DiagnosticEvent.MODEL_FAILED,e);mobileDraft?.close();mobileDraft=null;engineStatus=ui(e.message ?: "Loading failed");lastResult=engineStatus;enginePrefs.edit().putBoolean("enabled",false).apply()}
                            finally{modelLoading=false}
                        } else if(enginePrefs.getBoolean("enabled",false) && mobileDraft==null && energyAllowed()) {
                            Diagnostics.record(DiagnosticEvent.MODEL_LOADING)
                            modelLoading=true;engineReady=false
                            try {engineStatus=ui("Loading draft…");mobileDraft=MobileDraft(this).also { it.loadSaved() };engineStatus=ui("Draft ready · ARM64 CPU");Diagnostics.record(DiagnosticEvent.MODEL_READY)}
                            catch(e:Exception){Diagnostics.record(DiagnosticEvent.MODEL_FAILED,e);mobileDraft?.close();mobileDraft=null;enginePrefs.edit().putBoolean("enabled",false).apply();engineStatus=ui(e.message ?: "Loading failed")}
                            finally{modelLoading=false}
                        }
                        engineReady=mobileDraft?.ready==true && enginePrefs.getBoolean("enabled",false) && energyAllowed()
                        var job: JSONObject? = null
                        if(SystemClock.elapsedRealtime()-lastHeartbeat>=3000) {
                            val response = c.json("/v1/heartbeat", capabilities())
                            lastHeartbeat=SystemClock.elapsedRealtime()
                            job=response.optJSONObject("job")
                            if(!connected)Diagnostics.record(DiagnosticEvent.SESSION_CONNECTED)
                            connected=true;status = ui("Connected · node available")
                        }
                        if (job != null) runJob(c, job)
                        else if(mobileDraft?.ready==true && enginePrefs.getBoolean("enabled",false) && energyAllowed()) {
                            val work=JSONObject(String(c.bytes("/v1/engine/poll"),Charsets.UTF_8)).optJSONObject("work")
                            if(work!=null) {
                                val answer=if(energyAllowed() && enginePrefs.getBoolean("enabled",false)) mobileDraft!!.draft(work)
                                else JSONObject().apply {for(key in listOf("id","epoch","prefix_hash","tokenizer_fingerprint","model_sha256"))put(key,work.getString(key));put("error","Node paused to protect battery")}
                                if(stop.get()) break
                                if(!energyAllowed()) {answer.remove("tokens");answer.put("error","Draft paused to protect battery")}
                                c.json("/v1/engine/result",answer)
                            }
                        } else Thread.sleep(3000)
                        errors = 0
                    } catch (e: Exception) {
                        if (stop.get()) break
                        Diagnostics.record(DiagnosticEvent.SESSION_RETRY,e)
                        errors++;connected=false
                        status = ui("Connection interrupted · attempt {0}/3",errors)
                        if (errors >= 3) throw e
                        Thread.sleep(1000)
                    }
                }
            } catch (e: Exception) {
                if (!stop.get()) {Diagnostics.record(DiagnosticEvent.SESSION_FAILED,e);status = ui(connectionFailureMessage(e))}
            } finally {
                mobileDraft?.close();mobileDraft=null;engineStatus=ui("Draft unloaded from memory")
                if (generation.get() == runId) {running=false;connected=false;modelLoading=false;engineReady=false;downloadRequested.set(false)}
                stopSelfResult(startId)
            }
        }.also { it.start() }
        return START_NOT_STICKY
    }
    fun capabilities(): JSONObject {
        val mem = ActivityManager.MemoryInfo().also { getSystemService(ActivityManager::class.java).getMemoryInfo(it) }
        val battery = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val pct = battery?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val cm = getSystemService(ConnectivityManager::class.java)
        val network = cm.getNetworkCapabilities(cm.activeNetwork)
        val transport = when { network?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> "Wi-Fi / hotspot"; network?.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) == true -> "Ethernet"; network?.hasTransport(NetworkCapabilities.TRANSPORT_USB) == true -> "USB"; else -> "other / not detected" }
        val thermal = if (Build.VERSION.SDK_INT >= 29) getSystemService(PowerManager::class.java).currentThermalStatus else -1
        val thermalName = when(thermal) { 0 -> "nominal"; 1 -> "light"; 2 -> "moderate"; 3 -> "severe"; 4 -> "critical"; 5 -> "emergency"; 6 -> "shutdown"; else -> "unknown" }
        telemetry = ui("{0}\n{1}\n{2}", Build.MODEL,
            ui("Physical RAM: {0} GiB · available to system: {1} GiB", "%.1f".format(mem.totalMem/1073741824.0), "%.1f".format(mem.availMem/1073741824.0)),
            ui("{0} · thermal: {1}",ui(transport),ui(thermalName)))
        return JSONObject().put("model", "${Build.MANUFACTURER} ${Build.MODEL}").put("os", "Android ${Build.VERSION.RELEASE} / API ${Build.VERSION.SDK_INT}").put("app_version", packageManager.getPackageInfo(packageName, 0).versionName ?: "unknown").put("physical_memory_bytes", mem.totalMem).put("available_memory_bytes", mem.availMem).put("process_memory_bytes", Debug.getPss()*1024L).put("cpu_cores", Runtime.getRuntime().availableProcessors()).put("battery_percent", pct.coerceAtLeast(0)).put("thermal", thermalName).put("transport", transport).put("lifecycle", "foreground-service").put("supported_jobs", JSONArray(listOf("network", "network_paced", "cpu")))
            .put("engine_ready",mobileDraft?.ready==true && energyAllowed() && enginePrefs.getBoolean("enabled",false))
            .put("draft_sha256",mobileDraft?.sha256 ?: "").put("tokenizer_fingerprint",mobileDraft?.fingerprint ?: "")
    }
    private fun checkReady(started: Long) {
        check(!stop.get()) { "cancelled" }
        check(SystemClock.elapsedRealtime()-started < 90000) { "Measurement time limit exceeded" }
        if (Build.VERSION.SDK_INT >= 29) check(getSystemService(PowerManager::class.java).currentThermalStatus < PowerManager.THERMAL_STATUS_SEVERE) { "thermal_pause" }
    }
    private fun runJob(c: Client, job: JSONObject) {
        val samples = JSONArray()
        val started = SystemClock.elapsedRealtime()
        var outcome = "completed"
        var note = ""
        try {
            checkReady(started)
            if (job.getString("kind") in listOf("network", "network_paced")) {
                status = ui("Measuring network…")
                c.bytes("/v1/probe?size=64") // Warmup excluded.
                val paced = job.getString("kind") == "network_paced"
                for (pace in if (paced) listOf(0,30,60) else listOf(0)) {
                for (i in 0 until if (paced) 200 else 32) {
                    checkReady(started)
                    if (pace > 0) Thread.sleep(pace.toLong())
                    val t = SystemClock.elapsedRealtimeNanos()
                    val data = c.bytes("/v1/probe?size=64")
                    val ms = (SystemClock.elapsedRealtimeNanos()-t)/1e6
                    check(data.size == 64)
                    samples.put(JSONObject().put("kind", "rtt").put("bytes", 64).put("ms", ms).put("pace_ms",pace).put("connection_id",c.lastConnectionId))
                }
                }
                for (size in listOf(16384, 1048576)) {
                    val payload = ByteArray(size) { ((it*31+17) and 255).toByte() }
                    for (i in 0 until 4) {
                        checkReady(started)
                        var t = SystemClock.elapsedRealtimeNanos()
                        val data = c.bytes("/v1/probe?size=$size")
                        var ms = (SystemClock.elapsedRealtimeNanos()-t)/1e6
                        check(data.size == size)
                        samples.put(JSONObject().put("kind", "download").put("bytes", size).put("ms", ms))
                        checkReady(started)
                        t = SystemClock.elapsedRealtimeNanos()
                        val result = c.bytes("/v1/upload", payload, true)
                        ms = (SystemClock.elapsedRealtimeNanos()-t)/1e6
                        check(JSONObject(String(result)).getInt("bytes") == size)
                        samples.put(JSONObject().put("kind", "upload").put("bytes", size).put("ms", ms))
                    }
                }
                note = if (paced) "600 RTT samples grouped by 0/30/60 ms pauses; compare groups separately. Application-level HTTPS test, not LLM inference." else "Quick diagnostics: 32 RTT samples, exploratory p95. Warmup excluded; not an LLM benchmark."
                val measurements=(if(paced) listOf(0,30,60) else listOf(0)).map { pace ->
                    val rtts=(0 until samples.length()).map { samples.getJSONObject(it) }.filter {it.getString("kind")=="rtt" && it.optInt("pace_ms")==pace}.map{it.getDouble("ms")}.sorted()
                    ui("Pause {0} ms · p50 {1} · p95 {2} ms",pace,"%.2f".format(rtts[kotlin.math.ceil(rtts.size*.5).toInt()-1]),"%.2f".format(rtts[kotlin.math.ceil(rtts.size*.95).toInt()-1]))
                }
                lastResult=UiText(measurements.indices.joinToString("\n") { "{$it}" },measurements)
            } else if (job.getString("kind") == "cpu") {
                status = ui("Running synthetic CPU calibration…")
                val matrix = FloatArray(256*256) { ((it%97)-48)/97f }
                val vector = FloatArray(256) { (it%13)/13f }
                val out = FloatArray(256)
                val t = SystemClock.elapsedRealtimeNanos()
                var iterations = 0
                do {
                    checkReady(started)
                    vector[iterations%256] = (iterations%17)/17f
                    for (row in 0 until 256) { var sum = 0f; for (col in 0 until 256) sum += matrix[row*256+col]*vector[col]; out[row] = sum }
                    iterations++
                } while (SystemClock.elapsedRealtimeNanos()-t < 1_500_000_000L)
                val ms = (SystemClock.elapsedRealtimeNanos()-t)/1e6
                samples.put(JSONObject().put("kind", "cpu").put("iterations", iterations).put("ms", ms).put("checksum", abs(out.sum().toDouble())))
                note = "FP32 matvec 256×256, Kotlin/JVM, single thread. No tokens/s prediction."
                lastResult = ui("CPU · {0} iterations in {1} ms",iterations,"%.0f".format(ms))
            } else error("Unsupported job")
        } catch(e: Exception) {
            Diagnostics.record(DiagnosticEvent.JOB_FAILED,e)
            outcome = if (stop.get()) "cancelled" else if(e.message == "thermal_pause") "thermal_pause" else "failed"
            note = e.message ?: "Measurement interrupted"
            lastResult = ui("Measurement interrupted: {0}",ui(note))
        }
        if (!stop.get()) c.json("/v1/result", JSONObject().put("job_id", job.getString("id")).put("status", outcome).put("samples", samples).put("note", note))
    }
    override fun onDestroy() {
        Diagnostics.record(DiagnosticEvent.SESSION_STOP)
        mobileDraft?.cancel();connected=false;engineReady=false;downloadRequested.set(false)
        stop.set(true); client?.cancel(); worker?.interrupt()
        if(Build.VERSION.SDK_INT>=29) thermalListener?.let {getSystemService(PowerManager::class.java).removeThermalStatusListener(it)}
        if(worker==null && generation.get() == runId) running = false
        if (status.key in setOf("Connected · node available", "Measuring network…", "Running synthetic CPU calibration…", "Connecting to your computer…")) status = ui("Paused · no delegated work")
        super.onDestroy()
    }
}
