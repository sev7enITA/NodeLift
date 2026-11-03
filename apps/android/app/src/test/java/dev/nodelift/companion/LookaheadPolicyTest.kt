package dev.nodelift.companion
import org.junit.Assert.*
import org.junit.Test
class LookaheadPolicyTest {
    @Test fun matchesAuthoritativeBonusAndBoundsReuse() {
        val r=LookaheadPolicy.select(listOf(1,2),listOf(3,4,5),listOf(1,2,3),1,true,false)
        assertEquals(listOf(4),r.tokens);assertEquals(1,r.consumed);assertEquals(1,r.discarded)
    }
    @Test fun staleOrMismatchedPredictionsAreDiscarded() {
        for(prefix in listOf(listOf(1),listOf(1,9),listOf(1,2,9),listOf(1,2,3,4,5,6))) {
            val r=LookaheadPolicy.select(listOf(1,2),listOf(3,4,5),prefix,2,true,false)
            assertTrue(r.tokens.isEmpty());assertEquals(3,r.discarded);assertEquals(0,r.consumed)
        }
        assertEquals(3,LookaheadPolicy.select(listOf(1,2),listOf(3,4,5),listOf(1,2),2,false,false).discarded)
        assertEquals(3,LookaheadPolicy.select(listOf(1,2),listOf(3,4,5),listOf(1,2),2,true,true).discarded)
    }
    @Test fun fullyConsumedPredictionNeedsFreshDraft() {
        val r=LookaheadPolicy.select(listOf(1),listOf(2,3),listOf(1,2,3),2,true,false)
        assertTrue(r.tokens.isEmpty());assertEquals(2,r.consumed);assertEquals(0,r.discarded)
    }
}
