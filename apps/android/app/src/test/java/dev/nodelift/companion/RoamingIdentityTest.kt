package dev.nodelift.companion
import org.junit.Assert.*
import org.junit.Test
class RoamingIdentityTest {
    private val identity="nodelift-"+"a".repeat(32)+".local"
    @Test fun exactLogicalNameIsAccepted() {assertTrue(RoamingIdentity.matchesName(identity,listOf(identity)))}
    @Test fun wildcardAndDifferentIdentityFail() {
        assertFalse(RoamingIdentity.matchesName(identity,listOf("*.local")))
        assertFalse(RoamingIdentity.matchesName(identity,listOf("nodelift-"+"b".repeat(32)+".local")))
    }
    @Test fun transportIpIsNotAnIdentity() {assertFalse(RoamingIdentity.matchesName("192.168.1.1",listOf("192.168.1.1")))}
}
