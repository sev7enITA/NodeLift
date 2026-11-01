package dev.nodelift.companion
import org.junit.Assert.*
import org.junit.Test
class EnrollmentIdentityTest {
    @Test fun protocolVectorsMatchHost() {
        val root = ByteArray(32) { it.toByte() }
        assertEquals("b9fa84b70232336076070520d330d05e9d348e3db8ad759142fb0bdf868e8859", EnrollmentIdentity.scoped(root, "a".repeat(64)))
        assertEquals("ac2763917b36386ecf031135f4d02b0788d2aa65bd56c4abd02df4d252a5d3a4", EnrollmentIdentity.continuity("synthetic-test-token", "b".repeat(32)))
        assertNotEquals(EnrollmentIdentity.scoped(root,"a".repeat(64)),EnrollmentIdentity.scoped(root,"c".repeat(64)))
        assertNotEquals(EnrollmentIdentity.continuity("synthetic-test-token","b".repeat(32)),EnrollmentIdentity.continuity("synthetic-test-token","d".repeat(32)))
    }
}
