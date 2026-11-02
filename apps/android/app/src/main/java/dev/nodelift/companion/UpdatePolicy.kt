package dev.nodelift.companion

/** Public companion channel uses three numeric version components plus a monotonic build. */
data class CompanionRelease(val version:String,val build:Long) : Comparable<CompanionRelease> {
    private val parts=version.split('.').map { it.toLongOrNull() ?: -1 }
    init { require(version.matches(Regex("[0-9]{1,6}\\.[0-9]{1,6}\\.[0-9]{1,6}")) && build in 1..Int.MAX_VALUE) }
    override fun compareTo(other:CompanionRelease):Int {
        for(i in parts.indices) {val result=parts[i].compareTo(other.parts[i]);if(result!=0)return result}
        return build.compareTo(other.build)
    }
}
object UpdatePolicy {
    const val WEEK_MS=7*24*60*60*1000L
    const val RETRY_MS=60*60*1000L
    fun due(now:Long,lastSuccess:Long,lastAttempt:Long):Boolean {
        if(now<lastSuccess || now<lastAttempt)return true // Clock correction must not postpone indefinitely.
        return (lastSuccess<=0 || now-lastSuccess>=WEEK_MS) && (lastAttempt<=0 || now-lastAttempt>=RETRY_MS)
    }
}

/** Validated public metadata, never an instruction to install or a verified artifact payload. */
data class ReleaseDetails(val release:CompanionRelease,val date:String,val title:String,val changes:List<String>,val validation:String,val limitations:String,val artifact:String,val bytes:Long,val sha256:String,val url:String)
object ReleaseMetadata {
    private fun obj(value:Any?):Map<*,*> = value as? Map<*,*> ?: error("Expected object")
    private fun string(value:Any?,limit:Int):String {
        val s=value as? String ?: error("Expected string")
        require(s.isNotBlank() && s.length<=limit && s.none { it<' ' && it!='\n' && it!='\t' });return s
    }
    private fun integer(value:Any?,maximum:Long):Long {
        require(value is Int || value is Long);val n=(value as Number).toLong();require(n in 1..maximum);return n
    }
    fun parse(manifest:Map<*,*>,changelog:Map<*,*>,current:CompanionRelease):ReleaseDetails {
        val release=CompanionRelease(string(manifest["version"],32),integer(manifest["build"],Int.MAX_VALUE.toLong()))
        require(release>=current && release.build>=current.build)
        require(integer(changelog["schema_version"],1)==1L)
        val date=string(manifest["published_at"],32)
        require(date.matches(Regex("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")))
        java.time.Instant.parse(date)
        val entries=changelog["releases"] as? List<*> ?: error("Expected releases")
        require(entries.size in 1..256)
        require(obj(entries.first())["version"]==release.version && integer(obj(entries.first())["build"],Int.MAX_VALUE.toLong())==release.build)
        val matches=entries.map { obj(it) }.filter { it["version"]==release.version && it["build"] is Number && integer(it["build"],Int.MAX_VALUE.toLong())==release.build }
        require(matches.size==1)
        val notes=matches.single();require(notes["published_at"]==date)
        require(notes["url"]=="https://github.com/sev7enITA/NodeLift/releases/tag/v${release.version}")
        val changes=notes["changes"] as? List<*> ?: error("Expected changes")
        require(changes.size in 1..40)
        val name="NodeLift-${release.version}-android-debug.apk"
        val platform=obj(obj(manifest["platforms"])["android"])
        require(platform["artifact"]==name && platform["status"]=="compiled-debug-signed" && platform["architecture"]=="arm64-v8a")
        val asset=obj(obj(manifest["assets"])[name])
        val url="https://github.com/sev7enITA/NodeLift/releases/download/v${release.version}/$name"
        require(asset["url"]==url)
        val hash=string(asset["sha256"],64);require(hash.matches(Regex("[a-f0-9]{64}")))
        return ReleaseDetails(release,date,string(notes["title"],240),changes.map{string(it,4096)},string(notes["validation"],8192),string(notes["limitations"],8192),name,integer(asset["bytes"],2L*1024*1024*1024),hash,url)
    }
}
