import math
import random
import unittest

from nodelift.scheduling import AdaptiveDraftGate, PromptLookup


class GateTests(unittest.TestCase):
    def warmed(self):
        gate=AdaptiveDraftGate()
        for _ in range(4):
            self.assertEqual(gate.choose().route,'host')
            gate.observe_host(5,1)
        return gate

    def test_slower_draft_stops_after_probes_without_reentering(self):
        gate=self.warmed()
        for _ in range(2):
            self.assertEqual(gate.choose().reason,'bounded_probe')
            gate.observe_draft(30,3,4)
        self.assertEqual(gate.choose().reason,'no_measured_gain')
        for _ in range(8):gate.observe_host(100,1)
        self.assertEqual(gate.choose().route,'host')
        self.assertEqual(AdaptiveDraftGate().choose().reason,'calibrating_host')

    def test_profitable_draft_continues_but_detects_slowdown(self):
        gate=self.warmed()
        for _ in range(4):gate.observe_draft(8,4,4)
        self.assertEqual(gate.choose().reason,'measured_gain')
        gate.observe_draft(80,1,4)
        self.assertEqual(gate.choose().reason,'no_measured_gain')

    def test_discarded_work_counts_and_single_bad_probe_is_bounded(self):
        gate=self.warmed();gate.observe_draft(101,1,4)
        self.assertEqual(gate.choose().reason,'probe_cost_exceeded')
        gate=self.warmed()
        for _ in range(2):gate.observe_draft(20,1,4)
        self.assertEqual(gate.choose().draft_ms_per_token,20)
        self.assertEqual(gate.choose().route,'host')

    def test_deadline_and_failures(self):
        gate=self.warmed()
        self.assertEqual(gate.remote_timeout(4,30),.05)
        self.assertEqual(gate.remote_timeout(4,.03),.03)
        gate.disable('remote_failure')
        self.assertEqual(gate.choose().reason,'remote_failure')

    def test_invalid_observations_do_not_create_evidence(self):
        gate=AdaptiveDraftGate()
        for value in (0,-1,math.inf,math.nan):
            with self.assertRaises(ValueError):gate.observe_host(value,1)
        for count in (0,-1,True,1.5):
            with self.assertRaises(ValueError):gate.observe_draft(5,count,4)
        self.assertFalse(gate.host);self.assertFalse(gate.draft)


class LookupTests(unittest.TestCase):
    def test_exact_suffix_and_no_match(self):
        lookup=PromptLookup()
        self.assertEqual(lookup.propose([1,2,3,9,8,7,1,2,3],3),[9,8,7])
        self.assertEqual(PromptLookup().propose([1,2,3,4,5],4),[])

    def test_incremental_lookup_matches_independent_full_scan(self):
        rng=random.Random(71);prefix=[];lookup=PromptLookup()
        for _ in range(350):
            prefix.append(rng.randrange(4));count=rng.randint(1,16);expected=[]
            for size in range(min(8,len(prefix)),2,-1):
                matches=[start+size for start in range(len(prefix)-size)
                         if prefix[start:start+size]==prefix[-size:]]
                if matches:
                    expected=prefix[matches[-1]:matches[-1]+count];break
            self.assertEqual(lookup.propose(prefix,count),expected)
            self.assertTrue(all(token in prefix for token in expected))

    def test_context_and_budget_bounds(self):
        lookup=PromptLookup();lookup.propose([1,2,3],4)
        with self.assertRaises(ValueError):lookup.propose([1,2],4)
        for count in (0,17,True):
            with self.assertRaises(ValueError):PromptLookup().propose([1,2,3],count)


if __name__=='__main__':unittest.main()
