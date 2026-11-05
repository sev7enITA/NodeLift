package dev.nodelift.companion

/** Exact logical DNS identity, independent of the transport IP; wildcards are never accepted. */
object RoamingIdentity {
    fun matchesName(expected:String,names:List<String>):Boolean =
        expected.matches(Regex("nodelift-[0-9a-f]{32}\\.local")) && names.any {it==expected}
}
