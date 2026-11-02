package dev.nodelift.companion

import org.junit.Assert.*
import org.junit.Test

class ReleaseMetadataTest {
    private val current=CompanionRelease("0.2.10",12)
    private val name="NodeLift-0.2.10-android-debug.apk"
    private fun asset()=mutableMapOf<String,Any>("bytes" to 22242975L,"sha256" to "a".repeat(64),"url" to "https://github.com/sev7enITA/NodeLift/releases/download/v0.2.10/$name")
    private fun manifest(a:Map<String,Any> = asset())=mutableMapOf<String,Any>("version" to "0.2.10","build" to 12,"published_at" to "2026-11-01T23:18:55Z","assets" to mapOf(name to a),"platforms" to mapOf("android" to mapOf("artifact" to name,"status" to "compiled-debug-signed","architecture" to "arm64-v8a")))
    private fun notes()=mutableMapOf<String,Any>("version" to "0.2.10","build" to 12,"published_at" to "2026-11-01T23:18:55Z","title" to "Release","url" to "https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.10","changes" to listOf("An actual change"),"validation" to "Build only","limitations" to "No physical qualification")
    private fun log(n:Map<String,Any> = notes())=mapOf("schema_version" to 1,"releases" to listOf(n))
    @Test fun currentAndNewerReleasesAreReviewable() {
        val d=ReleaseMetadata.parse(manifest(),log(),current)
        assertEquals(current,d.release);assertEquals(name,d.artifact);assertEquals(22242975L,d.bytes)
        assertTrue(ReleaseMetadata.parse(manifest(),log(),CompanionRelease("0.2.9",11)).release>CompanionRelease("0.2.9",11))
        assertThrows(IllegalArgumentException::class.java){ReleaseMetadata.parse(manifest(),log(),CompanionRelease("0.2.11",13))}
    }
    @Test fun exactAssetUrlTypeSizeAndHashRequired() {
        for((key,value) in listOf("url" to "https://github.com.evil.test/sev7enITA/NodeLift", "url" to "https://github.com/sev7enITA/NodeLift/releases", "url" to asset()["url"].toString()+"?token=secret", "url" to asset()["url"].toString().replace("android-debug.apk","ios-unsigned.ipa"),"bytes" to true,"bytes" to "123","bytes" to 1.0,"bytes" to 0,"bytes" to 2147483649L,"sha256" to "a".repeat(63),"sha256" to "g".repeat(64))) {
            assertThrows(Exception::class.java){ReleaseMetadata.parse(manifest(asset().apply{put(key,value)}),log(),current)}
        }
    }
    @Test fun staleMismatchedDuplicateOrUnboundedNotesRejected() {
        for((key,value) in listOf("build" to 13,"build" to true,"build" to "12","published_at" to "2026-11-02T00:00:00Z","changes" to emptyList<String>(),"changes" to List(41){"change"},"limitations" to "x".repeat(8193),"title" to "\u0000unsafe")) {
            assertThrows(Exception::class.java){ReleaseMetadata.parse(manifest(),log(notes().apply{put(key,value)}),current)}
        }
        assertThrows(Exception::class.java){ReleaseMetadata.parse(manifest(),mapOf("schema_version" to 1,"releases" to listOf(notes(),notes())),current)}
        assertThrows(Exception::class.java){ReleaseMetadata.parse(manifest(),mapOf("schema_version" to 1,"releases" to listOf(notes().apply{put("version","0.2.11");put("build",13)},notes())),current)}
        for(value in listOf<Any>(true,"12",12.0,0,Int.MAX_VALUE.toLong()+1)) assertThrows(Exception::class.java){ReleaseMetadata.parse(manifest().apply{put("build",value)},log(),current)}
    }
}
