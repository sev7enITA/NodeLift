package dev.nodelift.companion

import java.io.File

/** Private bounded journal. No free-form exception messages or user data are accepted. */
enum class DiagnosticEvent {
    APP_START, UNCAUGHT_EXCEPTION, PREVIOUS_PROCESS_EXIT, SESSION_START, SESSION_CONNECTED,
    SESSION_RETRY, SESSION_FAILED, SESSION_STOP, CAMERA_OPEN, CAMERA_READY, CAMERA_FAILED,
    CAMERA_RESULT, MODEL_LOADING, MODEL_READY, MODEL_FAILED, JOB_FAILED, THERMAL_PAUSE,
    ROUTE_WIFI, ROUTE_ETHERNET, ROUTE_SYSTEM, UPDATE_CHECK, UPDATE_AVAILABLE, UPDATE_CURRENT, UPDATE_FAILED, EXPORT_FAILED
}

class DiagnosticStore(private val directory:File, private val build:Long=0, private val clock:()->Long = System::currentTimeMillis) {
    companion object { const val LIMIT=131072; const val RETENTION_MS=7*24*60*60*1000L }
    private var lastPrune=0L
    private fun prune() {
        val now=clock()
        if(lastPrune>0 && now>=lastPrune && now-lastPrune<3600000)return
        lastPrune=now
        val cutoff=now-RETENTION_MS
        for(file in files().filter{it.exists()}) {
            if(file.length()>LIMIT){file.delete();continue}
            val original=file.readLines()
            val kept=original.filter { line -> val time=Regex("^\\{\"time_ms\":(\\d+),").find(line)?.groupValues?.get(1)?.toLongOrNull();time!=null && time>=cutoff && time<=now }
            if(kept.isEmpty())file.delete() else if(kept.size!=original.size)file.writeText(kept.joinToString("\n",postfix="\n"))
        }
    }
    private fun files()=(0..2).map{File(directory,"events-$it.jsonl")}
    @Synchronized fun clear():Boolean { files().forEach{it.delete()};return files().none{it.exists()} }
    @Synchronized fun lines():List<String> {
        prune()
        val cutoff=clock()-RETENTION_MS
        return files().reversed().flatMap { file ->
            if(!file.exists() || file.length()>LIMIT) emptyList() else file.readLines().filter {
                val time=Regex("^\\{\"time_ms\":(\\d+),").find(it)?.groupValues?.get(1)?.toLongOrNull()
                time!=null && time>=cutoff && time<=clock()
            }
        }
    }
    @Synchronized fun append(event:DiagnosticEvent, error:Throwable?=null, code:Int?=null) {
        directory.mkdirs();prune()
        val entries=files()
        entries.filter{it.exists() && (it.lastModified()<clock()-RETENTION_MS || it.length()>LIMIT)}.forEach{it.delete()}
        val exception=error?.javaClass?.name?.takeIf{it.matches(Regex("[A-Za-z0-9_.$]{1,160}"))}
        // Method symbols and line numbers only. Never Throwable.message, file paths or thread names.
        val frames=error?.stackTrace?.filter{it.className.startsWith("dev.nodelift.")}?.take(12)?.mapNotNull {
            val symbol="${it.className}.${it.methodName}"
            if(symbol.matches(Regex("[A-Za-z0-9_.$<>-]{1,200}"))) "\"$symbol:${it.lineNumber.coerceAtLeast(0)}\"" else null
        } ?: emptyList()
        val line="{\"time_ms\":${clock()},\"reporter_build\":$build,\"event\":\"${event.name}\""+
            (exception?.let{",\"exception_type\":\"$it\""} ?: "")+
            (code?.let{",\"code\":$it"} ?: "")+",\"frames\":[${frames.joinToString(",") }]}\n"
        if(entries[0].length()+line.toByteArray(Charsets.UTF_8).size>LIMIT) {
            entries[2].delete();entries[1].renameTo(entries[2]);entries[0].renameTo(entries[1])
        }
        entries[0].appendText(line,Charsets.UTF_8)
    }
}
