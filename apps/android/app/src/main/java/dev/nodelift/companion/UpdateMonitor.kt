package dev.nodelift.companion

import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import org.json.JSONObject
import java.net.URL
import java.util.concurrent.Executors
import javax.net.ssl.HttpsURLConnection

/** One public manifest request; never attaches node credentials or device identifiers. */
object UpdateMonitor {
    private const val ENDPOINT="https://www.fabriziodegni.com/NodeLift/data/mobile-downloads.json"
    private val handler=Handler(Looper.getMainLooper())
    private val executor=Executors.newSingleThreadExecutor()
    @Volatile var checking=false;private set
    @Volatile var available=false;private set
    @Volatile var message:UiText=ui("Updates have not been checked yet.");private set
    private var started=false
    private var context:Context?=null
    private val timer=Runnable {context?.let { onResume(it) }}
    @Synchronized fun start(context:Context) {
        if(started)return
        started=true;this.context=context.applicationContext
        check(context) // Every new application process, even if last success was recent.
    }
    fun onResume(context:Context) {
        val prefs=context.getSharedPreferences("updates",0)
        if(UpdatePolicy.due(System.currentTimeMillis(),prefs.getLong("success",0),prefs.getLong("attempt",0)))check(context)
        else schedule(context)
    }
    private fun schedule(context:Context) {
        val prefs=context.getSharedPreferences("updates",0)
        val now=System.currentTimeMillis()
        val success=prefs.getLong("success",0);val attempt=prefs.getLong("attempt",0)
        val next=if(success>0 && now>=success && now-success<UpdatePolicy.WEEK_MS)success+UpdatePolicy.WEEK_MS else attempt+UpdatePolicy.RETRY_MS
        handler.removeCallbacks(timer)
        handler.postDelayed(timer,(next-now).coerceIn(1000,UpdatePolicy.WEEK_MS))
    }
    @Synchronized fun check(context:Context,manual:Boolean=false) {
        if(checking)return
        val app=context.applicationContext
        val prefs=app.getSharedPreferences("updates",0)
        // A manual action may retry immediately, but cannot fan out parallel requests.
        checking=true;message=ui("Checking for updates…")
        prefs.edit().putLong("attempt",System.currentTimeMillis()).apply()
        Diagnostics.record(DiagnosticEvent.UPDATE_CHECK)
        executor.execute {
            var connection:HttpsURLConnection?=null
            try {
                connection=URL(ENDPOINT).openConnection() as HttpsURLConnection
                connection.apply {connectTimeout=10000;readTimeout=10000;instanceFollowRedirects=false;useCaches=false;setRequestProperty("Accept","application/json");setRequestProperty("User-Agent","NodeLift-update-check")}
                require(connection.responseCode==200)
                val bytes=connection.inputStream.use{it.readBytesBounded(131072)}
                val manifest=JSONObject(String(bytes,Charsets.UTF_8))
                val release=CompanionRelease(manifest.getString("version"),manifest.get("build").toString().toLongOrNull() ?: error("Invalid build"))
                val info=app.packageManager.getPackageInfo(app.packageName,0)
                val current=CompanionRelease(info.versionName ?: error("Version unavailable"),if(Build.VERSION.SDK_INT>=28)info.longVersionCode else @Suppress("DEPRECATION") info.versionCode.toLong())
                available=release>current
                message=if(available)ui("Update available: {0} · build {1}",release.version,release.build) else ui("No newer companion release was found.")
                prefs.edit().putLong("success",System.currentTimeMillis()).apply()
                Diagnostics.record(if(available)DiagnosticEvent.UPDATE_AVAILABLE else DiagnosticEvent.UPDATE_CURRENT)
            } catch(error:Exception) {
                message=ui("Update check unavailable. Check your connection or try again later.")
                Diagnostics.record(DiagnosticEvent.UPDATE_FAILED,error)
            } finally {connection?.disconnect();checking=false;schedule(app)}
        }
    }
    private fun java.io.InputStream.readBytesBounded(limit:Int):ByteArray {
        val out=java.io.ByteArrayOutputStream();val buffer=ByteArray(4096)
        while(true) {val n=read(buffer);if(n<0)break;require(out.size()+n<=limit);out.write(buffer,0,n)}
        return out.toByteArray()
    }
}
