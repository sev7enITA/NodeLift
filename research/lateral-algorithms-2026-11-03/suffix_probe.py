"""Research-only candidate salvage. Never commits tokens or imports worker KV.

Call from a serialized target actor using one coherent host snapshot. The actor
must own the lease and keep its epoch/anchor unchanged through verifier dispatch.
This pure function does not supply that synchronization or a network protocol.
"""
from dataclasses import dataclass, replace
import math
import unittest


@dataclass(frozen=True)
class Scope:
    lease: str
    epoch: int
    worker: str
    target_hash: str
    draft_hash: str
    tokenizer_hash: str


@dataclass(frozen=True)
class Lease:
    scope: Scope
    anchor: tuple[int, ...]
    deadline: float  # host monotonic clock, never a worker timestamp
    max_candidates: int
    vocabulary_size: int
    context_limit: int
    terminal_ids: frozenset[int]


@dataclass(frozen=True)
class Proposal:
    scope: Scope
    anchor: tuple[int, ...]
    tokens: tuple[int, ...]


@dataclass(frozen=True)
class Decision:
    reason: str
    candidates: tuple[int, ...] = ()
    consumed_by_host: int = 0


def salvage(lease, packet, committed, *, now, remaining, cancelled=False):
    """Return unverified suffix candidates, or an explicit discard reason.

    Trusted host configuration and immutable token tuples are prerequisites.
    Network decoding/authentication and full metadata type validation precede
    this experiment. Only candidate token types are checked here explicitly.
    """
    if cancelled:
        return Decision('cancelled')
    if not math.isfinite(now) or not math.isfinite(lease.deadline) or now >= lease.deadline:
        return Decision('expired_or_invalid_clock')
    if packet.scope != lease.scope:
        return Decision('scope_mismatch')
    if packet.anchor != lease.anchor or not lease.anchor:
        return Decision('anchor_mismatch')
    if type(remaining) is not int or remaining < 1:
        return Decision('output_budget_exhausted')
    if not 1 <= len(packet.tokens) <= lease.max_candidates:
        return Decision('candidate_count_invalid')
    if any(type(t) is not int or not 0 <= t < lease.vocabulary_size for t in packet.tokens):
        return Decision('token_invalid')
    if any(t in lease.terminal_ids for t in packet.tokens[:-1]):
        return Decision('tokens_after_terminal')
    if len(lease.anchor) + len(packet.tokens) > lease.context_limit:
        return Decision('candidate_context_overflow')
    if len(committed) < len(lease.anchor) or committed[:len(lease.anchor)] != lease.anchor:
        return Decision('host_branch_changed')
    if committed[-1] in lease.terminal_ids:
        return Decision('host_terminal')
    m = len(committed) - len(lease.anchor)
    if m >= len(packet.tokens):
        return Decision('host_outran_candidate', consumed_by_host=m)
    if committed[len(lease.anchor):] != packet.tokens[:m]:
        return Decision('committed_overlap_mismatch')
    budget = min(remaining, lease.context_limit - len(committed))
    if budget <= 0:
        return Decision('context_exhausted')
    return Decision('send_suffix_to_verifier', packet.tokens[m:m + budget], m)


class ProtocolChecks(unittest.TestCase):
    def setUp(self):
        self.scope = Scope('lease-1', 7, 'worker-a', 'target-a', 'draft-a', 'vocab-a')
        self.lease = Lease(self.scope, (10, 11), 100.0, 8, 1000, 32, frozenset({999}))
        self.packet = Proposal(self.scope, (10, 11), (20, 21, 22, 23))

    def call(self, committed=(10, 11), **kwargs):
        return salvage(self.lease, self.packet, committed, now=kwargs.pop('now', 50.0),
                       remaining=kwargs.pop('remaining', 8), **kwargs)

    def test_progress_salvages_only_unverified_suffix(self):
        d = self.call((10, 11, 20, 21))
        self.assertEqual(d, Decision('send_suffix_to_verifier', (22, 23), 2))

    def test_no_progress_preserves_full_candidate_for_verification(self):
        self.assertEqual(self.call().candidates, self.packet.tokens)

    def test_already_committed_draft_work_gets_no_candidate_credit(self):
        self.assertFalse(self.call((10, 11, 20, 21, 22, 23)).candidates)

    def test_changed_committed_token_rejects_whole_packet(self):
        self.assertEqual(self.call((10, 11, 20, 77)).reason, 'committed_overlap_mismatch')

    def test_cancellation_and_expiry(self):
        self.assertFalse(self.call(cancelled=True).candidates)
        for now in (100.0, 101.0, float('nan'), float('inf')):
            self.assertFalse(self.call(now=now).candidates)

    def test_every_scope_dimension_fences_stale_work(self):
        for field in Scope.__dataclass_fields__:
            with self.subTest(field=field):
                stale = replace(self.scope, **{field: 8 if field == 'epoch' else 'changed'})
                self.assertFalse(salvage(self.lease, replace(self.packet, scope=stale),
                                         (10, 11), now=50, remaining=8).candidates)

    def test_lease_anchor_and_current_host_branch_both_matter(self):
        self.assertFalse(salvage(self.lease, replace(self.packet, anchor=(10, 12)),
                                (10, 11), now=50, remaining=8).candidates)
        self.assertFalse(self.call((10, 12)).candidates)
        self.assertFalse(self.call((10,)).candidates)

    def test_malformed_candidate_and_terminal_tail(self):
        for ids in ((), (True,), (-1,), (1000,), (20.0,), (20, 999, 22), tuple(range(9))):
            with self.subTest(ids=ids):
                self.assertFalse(salvage(self.lease, replace(self.packet, tokens=ids),
                                         (10, 11), now=50, remaining=8).candidates)

    def test_terminal_and_output_limits(self):
        self.assertFalse(self.call((10, 11, 999)).candidates)
        self.assertFalse(self.call(remaining=0).candidates)
        self.assertFalse(self.call(remaining=True).candidates)
        self.assertEqual(self.call((10, 11, 20), remaining=1).candidates, (21,))

    def test_candidate_cannot_exceed_dispatch_context(self):
        lease = replace(self.lease, context_limit=5)
        self.assertFalse(salvage(lease, self.packet, (10, 11), now=50, remaining=8).candidates)

    def test_unknown_future_token_still_requires_target_verifier(self):
        # This probe cannot tell whether 777 is a correct target continuation.
        p = replace(self.packet, tokens=(20, 777))
        self.assertEqual(salvage(self.lease, p, (10, 11, 20), now=50,
                                 remaining=8).candidates, (777,))

    def test_prefix_overlap_property_across_widths(self):
        for width in range(1, 9):
            ids = tuple(range(20, 20 + width)); p = replace(self.packet, tokens=ids)
            for advance in range(width):
                committed = self.lease.anchor + ids[:advance]
                d = salvage(self.lease, p, committed, now=50, remaining=8)
                self.assertEqual(committed + d.candidates, self.lease.anchor + ids)
                if advance:
                    altered = committed[:-1] + (777,)
                    self.assertFalse(salvage(self.lease, p, altered, now=50, remaining=8).candidates)


if __name__ == '__main__':
    unittest.main()
