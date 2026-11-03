package dev.nodelift.companion

import org.junit.Assert.*
import org.junit.Test
import java.nio.file.Files

class SupportPolicyTest {
    @Test fun releasesCompareNumericallyAndUseBuildForSameVersion() {
        assertTrue(CompanionRelease("0.10.0",1)>CompanionRelease("0.9.9",99))
        assertTrue(CompanionRelease("0.2.6",9)>CompanionRelease("0.2.6",8))
        assertFalse(CompanionRelease("0.2.5",99)>CompanionRelease("0.2.6",8))
        for(version in listOf("0.2", "v0.2.6", "0.2.6-beta", "https://bad.test", "9999999.0.0")) {
            assertThrows(IllegalArgumentException::class.java){CompanionRelease(version,1)}
        }
        assertThrows(IllegalArgumentException::class.java){CompanionRelease("0.2.6",0)}
    }
    @Test fun weeklyChecksAndOfflineRetryAreBoundedAndRecoverFromClockChanges() {
        val start=1_000_000L
        assertFalse(UpdatePolicy.due(start+UpdatePolicy.WEEK_MS-1,start,start))
        assertTrue(UpdatePolicy.due(start+UpdatePolicy.WEEK_MS,start,start))
        assertFalse(UpdatePolicy.due(start+1000,0,start))
        assertTrue(UpdatePolicy.due(start+UpdatePolicy.RETRY_MS,0,start))
        assertTrue(UpdatePolicy.due(start-1,start,start))
        assertTrue(UpdatePolicy.due(start,0,0))
    }
    @Test fun failedCheckAfterBackwardClockKeepsRetryCooldown() {
        val now=10_000_000L
        assertFalse(UpdatePolicy.due(now,now+UpdatePolicy.WEEK_MS,now-1000))
        assertFalse(UpdatePolicy.due(now+UpdatePolicy.RETRY_MS-1,now+UpdatePolicy.WEEK_MS,now))
        assertTrue(UpdatePolicy.due(now+UpdatePolicy.RETRY_MS,now+UpdatePolicy.WEEK_MS,now))
        assertTrue(UpdatePolicy.due(now,now+1000,now+1000))
    }
    @Test fun exceptionContentAndPathsNeverEnterJournalAndItSurvivesRestart() {
        val dir=Files.createTempDirectory("nodelift-diagnostics-").toFile()
        try {
            val secret="secret-pairing-123 prompt text https://192.168.1.2/key /private/model.gguf"
            val error=IllegalStateException(secret)
            error.stackTrace=arrayOf(StackTraceElement("dev.nodelift.companion.Scanner","open","/private/sensitive.kt",42),StackTraceElement("third.party.Library","request",secret,12))
            DiagnosticStore(dir){1000L}.append(DiagnosticEvent.CAMERA_FAILED,error)
            val text=DiagnosticStore(dir){1000L}.lines().joinToString()
            assertTrue(text.contains("Scanner.open:42"));assertTrue(text.contains("IllegalStateException"))
            for(forbidden in listOf("secret-pairing","prompt text","192.168","/private","third.party")) assertFalse(text.contains(forbidden))
        } finally {dir.deleteRecursively()}
    }
    @Test fun journalRotatesExpiresAndClears() {
        val dir=Files.createTempDirectory("nodelift-diagnostics-").toFile()
        try {
            var now=System.currentTimeMillis()
            val store=DiagnosticStore(dir){now}
            repeat(9000){store.append(DiagnosticEvent.SESSION_RETRY)}
            assertTrue(dir.listFiles()!!.size<=3)
            assertTrue(dir.listFiles()!!.all{it.length()<=DiagnosticStore.LIMIT})
            assertTrue(store.lines().isNotEmpty())
            now+=DiagnosticStore.RETENTION_MS+1
            assertTrue(store.lines().isEmpty())
            store.append(DiagnosticEvent.APP_START);assertEquals(1,store.lines().size)
            store.clear();assertTrue(store.lines().isEmpty())
        } finally{dir.deleteRecursively()}
    }
}
