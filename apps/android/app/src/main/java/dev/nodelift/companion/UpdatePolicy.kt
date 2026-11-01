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
