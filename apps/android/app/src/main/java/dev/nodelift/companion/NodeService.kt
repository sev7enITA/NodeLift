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
        @Volatile var running = false
        @Volatile var status = "Pronto per l’associazione"
        @Volatile var lastResult = "Nessuna misura eseguita"
        @Volatile var telemetry = ""
        val generation = AtomicLong(0)
    }
    private val stop = AtomicBoolean(false)
    private var worker: Thread? = null
    private var client: Client? = null
    private var runId = 0L
    override fun onBind(intent: Intent?) = null
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (running) return START_NOT_STICKY
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("session", "Sessione NodeLift", NotificationManager.IMPORTANCE_LOW))
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        startForeground(1, Notification.Builder(this, "session").setSmallIcon(dev.nodelift.companion.R.drawable.ic_node).setContentTitle("NodeLift · nodo attivo").setContentText("Misure autorizzate dal tuo computer. Apri per mettere in pausa.").setContentIntent(open).setOngoing(true).build())
        stop.set(false); running = true; runId = generation.incrementAndGet()
        val ticketText = intent?.getStringExtra("ticket")
        worker = Thread {
            try {
                status = "Connessione al computer…"
                val saved = if (ticketText == null) Vault.load(this) else null
                val ticket = Pairing.parse(if (ticketText != null) JSONObject(ticketText) else saved?.getJSONObject("pairing") ?: error("Incolla un invito dal computer."))
                val c = Client(ticket, saved?.optString("token") ?: ""); client = c
                if (ticketText != null) {
                    val response = c.json("/v1/pair", JSONObject().put("invite", ticket.invite).put("name", "${Build.MANUFACTURER} ${Build.MODEL}").put("capabilities", capabilities()))
                    c.token = response.getString("token")
                    Vault.save(this, JSONObject().put("pairing", ticket.json()).put("token", c.token).put("node_id", response.getString("node_id")))
                }
                var errors = 0
                while (!stop.get()) {
                    try {
                        val response = c.json("/v1/heartbeat", capabilities())
                        errors = 0
                        status = "Connesso · in attesa di una misura"
                        val job = response.optJSONObject("job")
                        if (job != null) runJob(c, job)
                    } catch (e: Exception) {
                        if (stop.get()) break
                        errors++
                        status = "Connessione interrotta · tentativo $errors/3"
                        if (errors >= 3) throw e
                    }
                    Thread.sleep(3000)
                }
            } catch (e: Exception) {
                if (!stop.get()) status = e.message ?: "Connessione non riuscita"
            } finally {
                if (generation.get() == runId) running = false
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
        val transport = when { network?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> "Wi-Fi / hotspot"; network?.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) == true -> "Ethernet"; network?.hasTransport(NetworkCapabilities.TRANSPORT_USB) == true -> "USB"; else -> "altro / non rilevato" }
        val thermal = if (Build.VERSION.SDK_INT >= 29) getSystemService(PowerManager::class.java).currentThermalStatus else -1
        val thermalName = when(thermal) { 0 -> "nominal"; 1 -> "light"; 2 -> "moderate"; 3 -> "severe"; 4 -> "critical"; 5 -> "emergency"; 6 -> "shutdown"; else -> "unknown" }
        telemetry = "${Build.MODEL}\nRAM fisica: %.1f GiB · disponibile al sistema: %.1f GiB\n%s · termica: %s".format(mem.totalMem/1073741824.0, mem.availMem/1073741824.0, transport, thermalName)
        return JSONObject().put("model", "${Build.MANUFACTURER} ${Build.MODEL}").put("os", "Android ${Build.VERSION.RELEASE} / API ${Build.VERSION.SDK_INT}").put("app_version", "0.1.0").put("physical_memory_bytes", mem.totalMem).put("available_memory_bytes", mem.availMem).put("process_memory_bytes", Debug.getPss()*1024L).put("cpu_cores", Runtime.getRuntime().availableProcessors()).put("battery_percent", pct.coerceAtLeast(0)).put("thermal", thermalName).put("transport", transport).put("lifecycle", "foreground-service").put("supported_jobs", JSONArray(listOf("network", "network_paced", "cpu")))
    }
    private fun checkReady(started: Long) {
        check(!stop.get()) { "cancelled" }
        check(SystemClock.elapsedRealtime()-started < 90000) { "Tempo massimo della misura superato" }
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
                status = "Misura rete in corso…"
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
                note = if (paced) "600 RTT in gruppi con pause 0/30/60ms; confrontare ogni gruppo separatamente. Test HTTPS applicativo, non LLM." else "Diagnostica breve: 32 RTT, p95 esplorativo. Warmup escluso; non è un benchmark LLM."
                val rtts = (0 until 32).map { samples.getJSONObject(it).getDouble("ms") }.sorted()
                lastResult = "Rete · p50 %.2f ms · p95 %.2f ms".format(rtts[15], rtts[30])
            } else if (job.getString("kind") == "cpu") {
                status = "Calibrazione CPU sintetica…"
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
                note = "FP32 matvec 256×256, Kotlin/JVM, singolo thread. Nessuna previsione token/s."
                lastResult = "CPU · $iterations iterazioni in %.0f ms".format(ms)
            } else error("Job non supportato")
        } catch(e: Exception) {
            outcome = if (stop.get()) "cancelled" else if(e.message == "thermal_pause") "thermal_pause" else "failed"
            note = e.message ?: "Misura interrotta"
            lastResult = "Misura interrotta: $note"
        }
        if (!stop.get()) c.json("/v1/result", JSONObject().put("job_id", job.getString("id")).put("status", outcome).put("samples", samples).put("note", note))
    }
    override fun onDestroy() {
        stop.set(true); client?.cancel(); worker?.interrupt()
        if (generation.get() == runId) running = false
        if (status.startsWith("Connesso") || status.contains("corso") || status.startsWith("Calibrazione")) status = "In pausa · nessun lavoro delegato"
        super.onDestroy()
    }
}
