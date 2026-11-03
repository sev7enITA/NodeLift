package dev.nodelift.companion

/** Exact prefix comparison; speculative tokens never authorize themselves. */
object LookaheadPolicy {
    data class Reuse(val tokens: List<Int>, val consumed: Int, val discarded: Int)
    fun select(base: List<Int>, predicted: List<Int>, committed: List<Int>, count: Int,
               identityMatches: Boolean, expired: Boolean): Reuse {
        require(count in 0..16 && predicted.size <= 17)
        val consumed = committed.size - base.size
        if (!identityMatches || expired || consumed < 0 || consumed > predicted.size ||
            committed != base + predicted.take(consumed)) return Reuse(emptyList(),0,predicted.size)
        val reuse = predicted.drop(consumed).take(count)
        return Reuse(reuse,consumed,predicted.size-consumed-reuse.size)
    }
}
