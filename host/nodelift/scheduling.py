"""Bounded local decisions from measured work. No cloud model or learned confidence.

The gate is an opt-in heuristic, not a statistical guarantee of speedup. Each
request starts fresh so another model, prompt, node or thermal state cannot
silently inherit a favorable decision. All proposed tokens still need target
verification. Timing includes discarded work and publication overhead.
"""
from collections import deque
from dataclasses import asdict, dataclass
import math
import statistics


@dataclass(frozen=True)
class DraftDecision:
    route: str
    reason: str
    host_samples: int
    draft_samples: int
    host_ms_per_token: float | None
    draft_ms_per_token: float | None

    def to_dict(self):
        return asdict(self)


class AdaptiveDraftGate:
    """Four useful host tokens, two bounded probes, then measured break-even.

    A 10% margin avoids treating timing ties as wins. A failed or unprofitable
    path stays off for the remainder of this request; the next request gets a
    new gate. The severe-loss guard can stop after one very expensive probe.
    These thresholds are engineering choices, not calibrated probabilities.
    """
    version = 'measured-gate-v1'
    host_warmup = 4
    probe_rounds = 2
    gain_margin = 0.10

    def __init__(self):
        self.host = deque(maxlen=8)
        self.draft = deque(maxlen=4)
        self.disabled_reason = None

    @staticmethod
    def _valid(milliseconds, generated):
        if not math.isfinite(milliseconds) or milliseconds <= 0 or type(generated) is not int or generated < 1:
            raise ValueError('timing observations require positive finite time and committed tokens')

    def observe_host(self, milliseconds, generated):
        self._valid(milliseconds, generated)
        self.host.append(milliseconds / generated)

    def observe_draft(self, milliseconds, generated, requested):
        self._valid(milliseconds, generated)
        self.draft.append((milliseconds, generated))
        baseline = statistics.median(self.host) if self.host else None
        if baseline and milliseconds > baseline * (requested + 1) * 4:
            self.disabled_reason = 'probe_cost_exceeded'

    def disable(self, reason):
        self.disabled_reason = reason

    def choose(self):
        baseline = statistics.median(self.host) if self.host else None
        draft_cost = (sum(t for t, _ in self.draft) / sum(n for _, n in self.draft)) if self.draft else None
        if self.disabled_reason:
            route, reason = 'host', self.disabled_reason
        elif len(self.host) < self.host_warmup:
            route, reason = 'host', 'calibrating_host'
        elif len(self.draft) < self.probe_rounds:
            route, reason = 'draft', 'bounded_probe'
        elif draft_cost >= baseline * (1 - self.gain_margin):
            self.disabled_reason = 'no_measured_gain'
            route, reason = 'host', self.disabled_reason
        else:
            route, reason = 'draft', 'measured_gain'
        return DraftDecision(route, reason, len(self.host), len(self.draft), baseline, draft_cost)

    def remote_timeout(self, count, configured_seconds):
        # The entire request deadline remains a hard ceiling. Two times the
        # optimistic host cost bounds an exploratory wait; no network retry.
        if not self.host:
            return configured_seconds
        return min(configured_seconds, max(.020, statistics.median(self.host) * (count + 1) * 2 / 1000))


class PromptLookup:
    """Incremental longest-suffix lookup over committed tokens only.

    Stores one most-recent occurrence per n-gram (3..8 tokens). No model, no
    external corpus and no speculative tokens enter the index. Memory is
    bounded by the request's context limit. Caller owns the append-only prefix.
    """
    def __init__(self, minimum=3, maximum=8):
        if not 1 <= minimum <= maximum <= 32:
            raise ValueError('invalid lookup n-gram limits')
        self.minimum, self.maximum = minimum, maximum
        self.index = {size: {} for size in range(minimum, maximum + 1)}
        self.indexed = 0

    def propose(self, prefix, count):
        if type(count) is not int or not 1 <= count <= 16:
            raise ValueError('invalid lookup budget')
        if len(prefix) < self.indexed:
            raise ValueError('lookup requires an append-only prefix')
        for size, entries in self.index.items():
            # Index only matches with at least one already committed follower.
            for start in range(max(0, self.indexed - size), len(prefix) - size):
                entries[tuple(prefix[start:start + size])] = start + size
        self.indexed = len(prefix)
        for size in range(min(self.maximum, len(prefix)), self.minimum - 1, -1):
            start = self.index[size].get(tuple(prefix[-size:]))
            if start is not None:
                return list(prefix[start:start + count])
        return []
