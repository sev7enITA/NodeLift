package dev.nodelift.companion

import android.app.Activity
import android.app.ActivityManager
import android.app.Application
import android.content.ClipData
import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.os.PowerManager
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class NodeLiftApplication:Application() {
    override fun onCreate() { super.onCreate();Diagnostics.start(this);UpdateMonitor.start(this) }
}

object Diagnostics {
    private var app:Context?=null
    private var store:DiagnosticStore?=null
    val hasPreviousIncident:Boolean get()=app?.getSharedPreferences("diagnostics",0)?.getBoolean("incident",false)==true
    @Synchronized fun start(context:Context) {
        if(app!=null)return
        app=context.applicationContext
        val packageInfo=context.packageManager.getPackageInfo(context.packageName,0)
        val build=if(Build.VERSION.SDK_INT>=28)packageInfo.longVersionCode else @Suppress("DEPRECATION") packageInfo.versionCode.toLong()
        store=DiagnosticStore(File(context.noBackupFilesDir,"diagnostics"),build)
        val previous=Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread,error ->
            try { context.getSharedPreferences("diagnostics",0).edit().putBoolean("incident",true).commit();record(DiagnosticEvent.UNCAUGHT_EXCEPTION,error) } catch(_:Throwable) {}
            // Retain Android's crash reporting and termination semantics. Never attempt recovery.
            if(previous!=null) previous.uncaughtException(thread,error)
            else { android.os.Process.killProcess(android.os.Process.myPid());kotlin.system.exitProcess(10) }
        }
        record(DiagnosticEvent.APP_START)
        if(Build.VERSION.SDK_INT>=30) try {
            val prefs=context.getSharedPreferences("diagnostics",0)
            val since=prefs.getLong("exit_checked",System.currentTimeMillis()-DiagnosticStore.RETENTION_MS)
            context.getSystemService(ActivityManager::class.java).getHistoricalProcessExitReasons(null,0,5)
                .filter{it.timestamp>since}.forEach {
                    // No OS description or raw tombstone: either can contain application data.
                    store?.append(DiagnosticEvent.PREVIOUS_PROCESS_EXIT,code=it.reason)
                    if(it.reason in listOf(android.app.ApplicationExitInfo.REASON_CRASH,android.app.ApplicationExitInfo.REASON_CRASH_NATIVE,android.app.ApplicationExitInfo.REASON_ANR))
                        prefs.edit().putBoolean("incident",true).apply()
                }
            prefs.edit().putLong("exit_checked",System.currentTimeMillis()).apply()
        } catch(_:Exception) {}
        pruneExports()
    }
    fun record(event:DiagnosticEvent,error:Throwable?=null) { try{store?.append(event,error)}catch(_:Exception){} }
    fun clear():Boolean = try {
        val journalCleared=store?.clear()==true
        pruneExports()
        val exportCleared=app?.let{File(it.cacheDir,"diagnostic-export").listFiles()?.isEmpty() ?: true} ?: false
        val cleared=journalCleared && exportCleared
        if(cleared)app?.getSharedPreferences("diagnostics",0)?.edit()?.putBoolean("incident",false)?.apply()
        cleared
    } catch(_:Exception){false}
    private fun pruneExports() {app?.let{File(it.cacheDir,"diagnostic-export").listFiles()?.forEach{file->file.delete()}}}
    fun export(activity:Activity):Boolean = try {
        val info=activity.packageManager.getPackageInfo(activity.packageName,0)
        val cm=activity.getSystemService(ConnectivityManager::class.java)
        val network=cm.getNetworkCapabilities(cm.activeNetwork)
        val transport=when {
            network==null->"offline"
            network.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)->"wifi"
            network.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)->"ethernet"
            network.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)->"cellular"
            else->"other"
        }
        @Suppress("DEPRECATION")
        val available = cm.allNetworks.mapNotNull { n -> cm.getNetworkCapabilities(n) }.flatMap { caps ->
            listOfNotNull(
                "wifi".takeIf { caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) },
                "ethernet".takeIf { caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) },
                "cellular".takeIf { caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) },
                "vpn".takeIf { caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN) })
        }.distinct()
        val report=JSONObject().put("schema","nodelift-diagnostics-v1").put("platform","android")
            .put("version",info.versionName).put("build",if(Build.VERSION.SDK_INT>=28)info.longVersionCode else @Suppress("DEPRECATION") info.versionCode.toLong())
            .put("api",Build.VERSION.SDK_INT).put("default_network_transport",transport)
            .put("available_network_transports",JSONArray(available))
            .put("thermal",if(Build.VERSION.SDK_INT>=29)activity.getSystemService(PowerManager::class.java).currentThermalStatus else -1)
            .put("session_running",NodeService.running).put("connected",NodeService.connected).put("engine_ready",NodeService.engineReady)
            .put("events",JSONArray((store?.lines() ?: emptyList()).map{JSONObject(it)}))
            .put("scope","Local allowlisted events. No prompts, credentials, QR data, addresses, model paths or raw crash dumps. Native crash details may be unavailable.")
        val dir=File(activity.cacheDir,"diagnostic-export").apply{mkdirs()}
        pruneExports()
        val file=File(dir,"NodeLift-diagnostics.json").apply{writeText(report.toString(2))}
        val uri=FileProvider.getUriForFile(activity,activity.packageName+".diagnostics",file)
        val share=Intent(Intent.ACTION_SEND).apply {
            type="application/json";putExtra(Intent.EXTRA_STREAM,uri);clipData=ClipData.newRawUri("NodeLift diagnostics",uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        activity.startActivity(Intent.createChooser(share,L10n.text(activity,"Export diagnostics")))
        true
    } catch(error:Exception){record(DiagnosticEvent.EXPORT_FAILED,error);false}
}
